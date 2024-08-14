"""Views for the user API"""

from rest_framework import generics, authentication, permissions
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


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user"""

    serializer_class = UserSerializer
    # meaning the view expects a token to authenticate users.
    # authentication is the process of verifying who a user is
    authentication_classes = (authentication.TokenAuthentication,)
    # ensures that only authenticated users can access this view
    # permission checks what an authenticated user is allowed to do
    permission_classes = (permissions.IsAuthenticated,)

    # this method is overridden to change the default behavior of retrieving an object by ID or other filters. Instead, it directly returns the authenticated user
    def get_object(self):
        """Retrieve and return authenticated user"""
        return (
            self.request.user
        )  # eturns the authenticated user  which is the user associated with the current session or token.
