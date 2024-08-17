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

    def _get_or_create_tags(self, tags, recipe):
        """Get or create tags for the recipe"""
        auth_user = self.context["request"].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(user=auth_user, **tag)
            recipe.tags.add(tag_obj)

    def create(self, validated_data):
        """Create a new recipe"""
        tags = validated_data.pop("tags", None)
        recipe = Recipe.objects.create(**validated_data)
        if tags:
            self._get_or_create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update a recipe"""
        tags = validated_data.pop("tags", None)
        # Ensure that tags key is present in the payload
        if tags is not None:
            instance.tags.clear()
            # Only recreate tags if the list is not empty
            if tags:
                self._get_or_create_tags(tags, instance)

        for key, value in validated_data.items():
            # set the attribute of the instance to the value
            # setattr is a built-in Python function used to set the value of an attribute of an object dynamically.
            # The first argument (instance) is the object whose attribute you want to set.
            # In this context, instance refers to the specific Recipe instance being updated.
            # The second argument (key) is the name of the attribute you want to set.
            # this corresponds to the keys in your validated_data dictionary,
            # which should match the field names of your Recipe model.
            # The third argument (value) is the value you want to set the attribute to.
            setattr(instance, key, value)
        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for the recipe detail object"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description"]
