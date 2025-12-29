import os
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Crew(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    class Meta:
        ordering = ("first_name", "last_name")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Airport(models.Model):
    name = models.CharField(max_length=100)
    closest_city = models.CharField(max_length=100)

    class Meta:
        unique_together = ("name", "closest_city")
        ordering = ("name", "closest_city")

    def __str__(self):
        return f"{self.name} ({self.closest_city} city)"


class Route(models.Model):
    source = models.ForeignKey(
        Airport, on_delete=models.CASCADE, related_name="routes"
    )
    destination = models.ForeignKey(
        Airport, on_delete=models.CASCADE, related_name="routes"
    )
    distance = models.PositiveIntegerField()

    class Meta:
        unique_together = ("source", "destination")

    def __str__(self):
        return f"{self.source} -> {self.destination}"


def create_airplane_type_image_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    path = f"{slugify(instance.name)}-{uuid.uuid4()}{ext}"
    return os.path.join("uploads/airplane_types/", path)


class AirplaneType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(
        upload_to=create_airplane_type_image_path, null=True, blank=True
    )

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Airplane(models.Model):
    name = models.CharField(max_length=100, unique=True)
    rows = models.PositiveIntegerField()
    seats_in_row = models.PositiveIntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType, on_delete=models.CASCADE, related_name="airplanes"
    )

    class Meta:
        ordering = ("name",)

    @property
    def capacity(self):
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class Flight(models.Model):
    route = models.ForeignKey(
        Route, on_delete=models.CASCADE, related_name="flights"
    )
    airplane = models.ForeignKey(
        Airplane, on_delete=models.CASCADE, related_name="flights"
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        ordering = ("departure_time",)

    @staticmethod
    def validate_datetime(departure_time, arrival_time, error_to_raise):
        if departure_time > arrival_time:
            raise error_to_raise(
                "Departure time must be earlier than Arrival time"
            )

    def clean(self):
        Flight.validate_datetime(
            self.departure_time,
            self.arrival_time,
            error_to_raise=ValidationError,
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Flight {str(self.route)}"
            f"({str(self.departure_time)} - {str(self.arrival_time)})"
        )


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="orders"
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return str(self.created_at)


class Ticket(models.Model):
    row = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()
    flight = models.ForeignKey(
        Flight, on_delete=models.CASCADE, related_name="tickets"
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="tickets"
    )

    class Meta:
        ordering = ("flight", "row", "seat")
        unique_together = ("flight", "row", "seat")

    @staticmethod
    def validate_seats(row, seat, airplane, error_to_raise):
        for value, value_name, attr_name in (
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ):
            attr_value = getattr(airplane, attr_name)
            if 1 <= value <= attr_value:
                raise error_to_raise(
                    {
                        value_name: f"{value_name} "
                        f"number must be in available range: "
                        f"(1, {attr_name}): "
                        f"(1, {attr_value})"
                    }
                )

    def clean(self):
        Ticket.validate_seats(
            self.row, self.seat, self.flight.airplane, ValidationError
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{str(self.flight)} (row: {self.row}, seat: {self.seat})"
