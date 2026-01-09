from django.db.models import Prefetch, F, Count
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import status
from rest_framework import mixins

from airport.models import (
    Crew,
    Airport,
    Route,
    AirplaneType,
    Airplane,
    Flight,
    Order,
    Ticket,
)
from airport.permissions import AuthenticatedReadCreate
from airport.serializers import (
    CrewSerializer,
    AirportSerializer,
    RouteSerializer,
    RouteReadSerializer,
    AirplaneTypeSerializer,
    AirplaneTypeImageSerializer,
    AirplaneSerializer,
    AirplaneReadSerializer,
    FlightSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    OrderSerializer,
    OrderAdminDetailSerializer,
    OrderReadSerializer,
)


class CrewViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Crew.objects.prefetch_related(
        Prefetch(
            "flights",
            queryset=Flight.objects.select_related(
                "route__source",
                "route__destination",
            ),
        )
    )
    serializer_class = CrewSerializer


class AirportViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer


class RouteViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Route.objects.select_related("source", "destination")

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RouteReadSerializer
        return RouteSerializer


class AirplaneTypeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    queryset = AirplaneType.objects.all()

    def get_serializer_class(self):
        if self.action == "upload_image":
            return AirplaneTypeImageSerializer
        return AirplaneTypeSerializer

    @action(
        detail=True,
        methods=["POST"],
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk):
        """Action to upload an image for AirplaneType"""
        airplane_type = self.get_object()
        serializer = AirplaneTypeImageSerializer(
            airplane_type, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class AirplaneViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Airplane.objects.select_related("airplane_type")

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return AirplaneReadSerializer
        return AirplaneSerializer


class FlightViewSet(ModelViewSet):
    queryset = Flight.objects.prefetch_related("crew").select_related(
        "airplane__airplane_type",
        "route__destination",
        "route__source",
    )

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightDetailSerializer
        return FlightSerializer

    def get_queryset(self):
        qs = self.queryset
        if self.action in ("list", "retrieve"):
            qs = qs.annotate(
                available_seats=(
                    F("airplane__rows") * F("airplane__seats_in_row")
                    - Count("tickets")
                )
            )
        if self.action == "retrieve":
            qs = qs.prefetch_related("tickets")

        if self.action == "list":
            if sources := self.request.query_params.get("sources"):
                qs = qs.filter(
                    route__source__closest_city__in=sources.split(",")
                )
            if destinations := self.request.query_params.get("destinations"):
                qs = qs.filter(
                    route__destination__closest_city__in=destinations.split(
                        ","
                    )
                )
            if date := self.request.query_params.get("date"):
                qs = qs.filter(departure_time__date=date)
        return qs

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="sources",
                type=type("array"),
                many=True,
                description="filter flights by source cities airports",
            ),
            OpenApiParameter(
                name="destinations",
                type=type("array"),
                many=True,
                description="filter flights by destination cities airports",
            ),
            OpenApiParameter(
                name="date",
                type=str,
                many=False,
                description="filter flights by departure "
                            "time in YYYY-MM-DD format",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    permission_classes = [IsAdminUser | AuthenticatedReadCreate]
    queryset = Order.objects.prefetch_related(
        Prefetch(
            "tickets",
            queryset=Ticket.objects.select_related(
                "flight__route__source", "flight__route__destination"
            ),
        )
    )

    def get_serializer_class(self):
        if self.action == "retrieve" and self.request.user.is_staff:
            return OrderAdminDetailSerializer
        if self.action in ("list", "retrieve"):
            return OrderReadSerializer
        return OrderSerializer

    def get_queryset(self):
        qs = self.queryset
        if self.action == "retrieve" and self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """Admins can retrieve order details of any User.
        By default, User can retrieve only their own orders."""
        return super().retrieve(request, *args, **kwargs)
