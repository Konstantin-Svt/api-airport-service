from django.urls import include, path
from rest_framework.routers import DefaultRouter

from airport.views import (
    RouteViewSet,
    CrewViewSet,
    AirportViewSet,
    AirplaneTypeViewSet,
    AirplaneViewSet,
    FlightViewSet,
    OrderViewSet,
)

app_name = "airport"

router = DefaultRouter()
router.register("routes", RouteViewSet)
router.register("crew", CrewViewSet)
router.register("airports", AirportViewSet)
router.register("airplane_types", AirplaneTypeViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("flights", FlightViewSet)
router.register("orders", OrderViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
