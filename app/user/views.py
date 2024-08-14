"""Views for the user API"""

from rest_framework import generics
from .serializers import UserSerializer, AuthTokenSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""

    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user"""

    # we override the ObtainAuthToken view to use our custom AuthToken because it uses username field instead of email
    serializer_class = AuthTokenSerializer
    renderer_classes = (
        api_settings.DEFAULT_RENDERER_CLASSES
    )  # to make the view browsable
