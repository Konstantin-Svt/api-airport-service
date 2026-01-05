from django.contrib import admin
from django.contrib.admin import TabularInline

from airport.models import (
    Airport,
    Airplane,
    AirplaneType,
    Crew,
    Flight,
    Order,
    Ticket,
    Route,
)


admin.site.register(Airport)
admin.site.register(Airplane)
admin.site.register(AirplaneType)
admin.site.register(Crew)
admin.site.register(Ticket)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    search_fields = ("source__name", "destination__name")


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    autocomplete_fields = ("route",)
    search_fields = (
        "route",
        "departure_time",
        "arrival_time",
    )

    def get_queryset(self, request):
        return Flight.objects.select_related(
            "route__source",
            "route__destination",
            "airplane__airplane_type",
        ).prefetch_related(
            "crew",
        )


class TicketInline(TabularInline):
    model = Ticket
    extra = 1
    autocomplete_fields = ("flight",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "flight__route__source", "flight__route__destination"
        )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = (TicketInline,)
