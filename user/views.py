from django.db import transaction
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)

from user.serializers import UserSerializer


class UserCreateView(CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


class UserManageView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class ResetTokenAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            request.user.token_version += 1
            request.user.save()
            tokens = OutstandingToken.objects.filter(user=request.user)
            for token in tokens:
                BlacklistedToken.objects.create(token=token)
            return Response(status=status.HTTP_205_RESET_CONTENT)
