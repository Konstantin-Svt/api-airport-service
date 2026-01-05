import os
import shutil
import tempfile
from datetime import datetime

from PIL import Image
from django.contrib.auth import get_user_model
from django.db.models import Count, F
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import AirplaneType, Airplane, Airport, Route, Flight
from airport.serializers import (
    FlightListSerializer,
    FlightDetailSerializer,
)


annotated_flights = Flight.objects.all().annotate(
    available_seats=(
        F("airplane__rows") * F("airplane__seats_in_row") - Count("tickets")
    )
)


class TestFlightAPIView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()
        cls.airplane_type = AirplaneType.objects.create(name="AirplaneType1")
        cls.destination = Airport.objects.create(
            name="TestDestinationPort", closest_city="TestDestinationCity"
        )
        cls.source = Airport.objects.create(
            name="TestSourcePort", closest_city="TestSourceCity"
        )
        cls.route = Route.objects.create(
            source=cls.source, destination=cls.destination, distance=100
        )
        cls.airplane = Airplane.objects.create(
            name="TestAirplane",
            rows=2,
            seats_in_row=10,
            airplane_type=cls.airplane_type,
        )

    def setUp(self):
        self.user_admin = get_user_model().objects.create_superuser(
            email="admin@admin", password="admin"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user_admin)
        self.flight = Flight.objects.create(
            route=self.route,
            airplane=self.airplane,
            departure_time=datetime(year=2025, month=12, day=30),
            arrival_time=datetime(year=2025, month=12, day=31),
        )

    def test_get_flight_list(self):
        response = self.client.get(reverse("airport:flight-list"))
        serializer = FlightListSerializer(annotated_flights, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, response.data)

    def test_search_flight_by_source_cities(self):
        not_searched_port = Airport.objects.create(
            name="NotSearchedPort", closest_city="NotSearchedCity"
        )
        not_searched_route = Route.objects.create(
            source=not_searched_port,
            destination=self.destination,
            distance=100,
        )
        Flight.objects.create(
            route=not_searched_route,
            airplane=self.airplane,
            departure_time=datetime(year=2025, month=12, day=30),
            arrival_time=datetime(year=2025, month=12, day=31),
        )
        response = self.client.get(
            reverse("airport:flight-list"),
            query_params={"sources": "TestSourceCity,Fake"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "TestSourcePort")
        self.assertNotContains(response, "NotSearchedPort")

    def test_search_flight_by_destination_cities(self):
        not_searched_port = Airport.objects.create(
            name="NotSearchedPort", closest_city="NotSearchedCity"
        )
        not_searched_route = Route.objects.create(
            source=self.source,
            destination=not_searched_port,
            distance=100,
        )
        Flight.objects.create(
            route=not_searched_route,
            airplane=self.airplane,
            departure_time=datetime(year=2025, month=12, day=30),
            arrival_time=datetime(year=2025, month=12, day=31),
        )
        response = self.client.get(
            reverse("airport:flight-list"),
            query_params={"destinations": "TestDestinationCity,Fake"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "TestDestinationPort")
        self.assertNotContains(response, "NotSearchedPort")

    def test_search_flight_by_departure_date(self):
        not_searched_port = Airport.objects.create(
            name="NotSearchedPort", closest_city="NotSearchedCity"
        )
        not_searched_route = Route.objects.create(
            source=self.source,
            destination=not_searched_port,
            distance=100,
        )
        Flight.objects.create(
            route=not_searched_route,
            airplane=self.airplane,
            departure_time=datetime(year=2025, month=12, day=18),
            arrival_time=datetime(year=2025, month=12, day=19),
        )
        response = self.client.get(
            reverse("airport:flight-list"), query_params={"date": "2025-12-30"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "TestDestinationPort")
        self.assertNotContains(response, "NotSearchedPort")

    def test_admin_only_flight_create(self):
        response = self.client.post(
            reverse("airport:flight-list"),
            data={
                "airplane": self.airplane.id,
                "departure_time": datetime(year=2025, month=11, day=10),
                "arrival_time": datetime(year=2025, month=11, day=11),
                "route": self.route.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user_admin.is_staff = False
        response = self.client.post(
            reverse("airport:flight-list"),
            data={
                "airplane": self.airplane.id,
                "departure_time": datetime(year=2025, month=12, day=10),
                "arrival_time": datetime(year=2025, month=12, day=11),
                "route": self.route.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_flight_arrival_earlier_departure(self):
        response = self.client.post(
            reverse("airport:flight-list"),
            data={
                "airplane": self.airplane.id,
                "departure_time": datetime(year=2025, month=11, day=15),
                "arrival_time": datetime(year=2025, month=11, day=11),
                "route": self.route.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_flight_retrieve(self):
        response = self.client.get(
            reverse("airport:flight-detail", kwargs={"pk": 1})
        )
        serializer = FlightDetailSerializer(
            instance=Flight.objects.filter(pk=self.flight.id)
            .annotate(
                available_seats=(
                    F("airplane__rows") * F("airplane__seats_in_row")
                    - Count("tickets")
                )
            )
            .first()
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)


TEMPDIR = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMPDIR)
class TestAirplaneTypeImage(TestCase):
    def setUp(self):
        self.airplane_type = AirplaneType.objects.create(
            name="TestAirplaneType"
        )
        self.user_admin = get_user_model().objects.create_superuser(
            email="admin@admin", password="admin"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user_admin)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMPDIR, ignore_errors=True)

    def test_flight_image_upload(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new(mode="RGB", size=(10, 10), color="black")
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            response = self.client.post(
                reverse(
                    "airport:airplanetype-upload-image",
                    kwargs={"pk": self.airplane_type.id},
                ),
                data={"image": ntf},
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("image"))

        self.airplane_type.refresh_from_db()
        self.assertTrue(os.path.exists(self.airplane_type.image.path))
