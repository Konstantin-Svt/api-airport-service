from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user.serializers import UserSerializer


class TestUser(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user_with_email_as_username(self):
        response = self.client.post(
            reverse("user:register"),
            data={
                "email": "user@user.com",
                "password": "TestingTest1234",
            },
        )
        serializer = UserSerializer(
            instance=get_user_model().objects.get(email="user@user.com")
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(serializer.data, response.data)

    def test_email_unique_required(self):
        get_user_model().objects.create_user(
            email="user@user.com", password="12345"
        )
        response = self.client.post(
            reverse("user:register"),
            data={
                "email": "user@user.com",
                "password": "TestingTest1234",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
