"""
Serializers for recipe APIs
"""

from rest_framework import serializers
from core.models import Recipe, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects"""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for the recipe object"""

    # default read_only is true
    # so we need to apply custom logic to be able to update the tags and create new tags with the recipe
    # nested serializer
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        # we want to return the tags with the recipe
        fields = ["id", "title", "time_minutes", "price", "link", "tags"]
        # we don't want the user to update the id or create a new recipe with a specific id
        read_only_fields = ["id"]

    def create(self, validated_data):
        """Create a new recipe"""
        tags = validated_data.pop("tags", None)
        recipe = Recipe.objects.create(**validated_data)
        auth_user = self.context["request"].user
        if tags:
            for tag in tags:
                tag_obj, created = Tag.objects.get_or_create(user=auth_user, **tag)
                recipe.tags.add(tag_obj)
        return recipe


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for the recipe detail object"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description"]
