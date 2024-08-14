"""
Serializers for the user API Views
"""

from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import ugettext_lazy as _
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


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user authentication object"""
    email = serializers.CharField()
    password = serializers.CharField(
        style={"input_type": "password"},  # Makes the password field in the browsable API a password field
        trim_whitespace=False  # Allows whitespace in the password
    )

    def validate(self, attrs):  # Called when we validate the serializer; overridden to validate authentication
        """
        Validate and authenticate the user.
        This method is called during the validation process to enforce custom validation logic.
        """
        email = attrs.get("email")
        password = attrs.get("password")

        # Authenticate the user with the provided email and password using Django's authenticate function
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password
        )

        if not user:
            # If authentication fails, raise a ValidationError with an appropriate error message
            msg = _("Unable to authenticate with provided credentials")
            raise serializers.ValidationError(msg, code="authentication")

        # If authentication succeeds, add the authenticated user to the validated data (attrs)
        attrs["user"] = user
        return attrs

        # Default Behavior of validate Method:
        # By default, serializers in Django REST Framework (DRF) do not have a validate method implemented.
        # However, DRF provides a validate method that you can override to add custom validation logic.
        # The default validate method simply returns the validated data (attrs) as is, without any additional checks.
        # Overriding the validate method allows you to add logic to ensure that the data meets certain conditions before being considered valid.

        # Custom Behavior in AuthTokenSerializer:
        # The AuthTokenSerializer overrides the validate method to include custom validation logic for authenticating a user.
        # This involves:
        # - Retrieving the email and password from the input data.
        # - Using Django's authenticate function to verify the credentials.
        # - If the authentication fails, raising a ValidationError with an appropriate error message.
        # - If the authentication succeeds, adding the authenticated user to the validated data (attrs).
