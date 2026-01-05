from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DatabaseValidationError

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


class CrewSerializer(serializers.ModelSerializer):
    flights = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "full_name", "flights")


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "closest_city")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")

    def validate(self, data):
        super().validate(data)
        Route.validate_airports(
            data["source"], data["destination"], ValidationError
        )
        return data


class RouteReadSerializer(RouteSerializer):
    source = AirportSerializer(read_only=True)
    destination = AirportSerializer(read_only=True)


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name", "image")
        read_only_fields = ("id", "image")


class AirplaneTypeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "image")


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "capacity",
            "airplane_type",
        )


class AirplaneReadSerializer(AirplaneSerializer):
    airplane_type = AirplaneTypeSerializer(read_only=True)


class FlightSerializer(serializers.ModelSerializer):
    route = serializers.PrimaryKeyRelatedField(
        queryset=Route.objects.select_related("source", "destination")
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "airplane",
            "route",
            "departure_time",
            "arrival_time",
            "crew",
        )

    def validate(self, data):
        super().validate(data)
        Flight.validate_datetime(
            data["departure_time"], data["arrival_time"], ValidationError
        )
        return data


class FlightListSerializer(FlightSerializer):
    airplane_type = serializers.CharField(
        read_only=True, source="airplane.airplane_type.name"
    )
    airplane_capacity = serializers.IntegerField(
        read_only=True, source="airplane.capacity"
    )
    available_seats = serializers.IntegerField(read_only=True)
    airplane_type_image = serializers.ImageField(
        read_only=True, source="airplane.airplane_type.image"
    )
    route = serializers.StringRelatedField(read_only=True)
    crew = serializers.StringRelatedField(read_only=True, many=True)

    class Meta(FlightSerializer.Meta):
        fields = (
            "id",
            "airplane_type",
            "airplane_type_image",
            "airplane_capacity",
            "available_seats",
            "route",
            "departure_time",
            "arrival_time",
            "crew",
        )


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "flight")

    def validate(self, data):
        super().validate(data)
        Ticket.validate_seats(
            data["row"], data["seat"], data["flight"].airplane, ValidationError
        )
        return data


class TicketFlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class TicketListSerializer(TicketSerializer):
    flight = serializers.StringRelatedField(read_only=True)


class FlightDetailSerializer(FlightSerializer):
    airplane = AirplaneReadSerializer(read_only=True)
    available_seats = serializers.IntegerField(read_only=True)
    route = serializers.StringRelatedField(read_only=True)
    crew = serializers.StringRelatedField(read_only=True, many=True)
    sold_tickets = TicketFlightSerializer(
        read_only=True, many=True, source="tickets"
    )

    class Meta(FlightSerializer.Meta):
        fields = FlightSerializer.Meta.fields + (
            "available_seats",
            "sold_tickets",
        )


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(read_only=False, required=True, many=True)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")

    def create(self, validated_data):
        with transaction.atomic():
            tickets = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket in tickets:
                try:
                    tk = Ticket.objects.create(order=order, **ticket)
                except DatabaseValidationError:
                    raise ValidationError(
                        {
                            f"row={tk.row}, "
                            f"seat={tk.seat}, "
                            f"flight={tk.flight.id}":
                                "Tickets must be unique. "
                                "This ticket has duplicates in this order."
                        }
                    )
            return order


class OrderReadSerializer(serializers.ModelSerializer):
    tickets = TicketListSerializer(read_only=True, many=True)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")


class OrderAdminDetailSerializer(OrderReadSerializer):
    tickets = TicketListSerializer(read_only=False, many=True)

    class Meta(OrderReadSerializer.Meta):
        fields = OrderReadSerializer.Meta.fields + ("user",)
