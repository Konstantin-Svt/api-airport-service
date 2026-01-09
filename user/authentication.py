from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class TVJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            user, token = super().authenticate(request)
        except TypeError:
            return None
        if token.get("tv") != user.token_version:
            raise AuthenticationFailed("Token is invalid!!")
        return user, token
