"""
Serializers for the user API Views
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the users object"""

    class Meta:
        model = get_user_model()
        # we would not want to include is_staff and is_superuser in the response because we don't want user to set for themselves, they should be set by the admin
        fields = ("email", "password", "name")
        # in return, we don't want to include password in the response
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    # it overrides the create function of the ModelSerializer class to create a user with encrypted password
    # normally, the create function of the ModelSerializer class would just create a user with the password in plain text
    def create(self, validated_data):
        """Create a new user with encrypted password and return it"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update a user, setting the password correctly and return it"""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user
