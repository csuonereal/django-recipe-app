"""
Test cases for models
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from core import models


class ModelTests(TestCase):
    """Test models"""

    def test_create_user_with_email_successful(self):
        """
        Test creating a new user with an email is successful
        """
        email = "test@example.com"
        password = "Passw0rd!"
        # we should implement custom user model to use email instead of username
        user = get_user_model().objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """
        Test the email for a new user is normalized
        """
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@example.com", "test4@example.com"],
        ]
        password = "Passw0rd!"

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, password)
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """
        Test creating user without email raises error
        """
        password = "Passw0rd!"
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, password)

    def test_create_superuser(self):
        """
        Test creating a new superuser
        """
        email = "superuser@example.com"
        password = "Passw0rd!"
        user = get_user_model().objects.create_superuser(email, password)
        self.assertTrue(user.is_superuser)  # allows every permission
        self.assertTrue(user.is_staff)  # allows user to login to admin site

    def test_create_recipe(self):
        """
        Test creating a new recipe successfully
        """
        user = get_user_model().objects.create_user(
            email="test@example.com", password="Passw0rd!"
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title="Steak and mushroom sauce",
            time_minutes=5,
            price=Decimal("5.50"),
            description="Nice and tasty",
        )
        self.assertEqual(str(recipe), recipe.title)
