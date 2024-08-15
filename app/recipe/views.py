"""
Views for the recipe APIs
"""

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Recipe
from recipe import serializers


class RecipeViewSet(viewsets.ModelViewSet):
    """Manage recipes in the database"""

    serializer_class = serializers.RecipeSerializer
    queryset = (
        Recipe.objects.all()
    )  # we want to get all the recipes, queryset represents the objects that we want to manage
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Return recipes for the current authenticated user only"""
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)
