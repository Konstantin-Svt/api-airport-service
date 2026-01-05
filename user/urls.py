from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from user.views import UserCreateView, UserManageView


app_name = "user"

urlpatterns = [
    path("register/", UserCreateView.as_view(), name="register"),
    path("me/", UserManageView.as_view(), name="me"),
    path(
        "token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]
