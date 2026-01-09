from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, AuthUser
from rest_framework_simplejwt.tokens import Token


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, min_length=5
    )

    class Meta:
        model = get_user_model()
        fields = ("id", "email", "password", "is_staff")
        read_only_fields = ("id", "is_staff")

    def create(self, validated_data):
        user = get_user_model().objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get("email", instance.email)
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class TVTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: AuthUser) -> Token:
        token = super().get_token(user)
        token["tv"] = user.token_version
        return token
