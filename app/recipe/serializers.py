"""
Serializers for recipe APIs
"""

from rest_framework import serializers
from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for the recipe object"""

    class Meta:
        model = Recipe
        fields = ("id", "title", "time_minutes", "price", "link")
        read_only_fields = (
            "id",
        )  # we don't want the user to update the id or create a new recipe with a specific id
