"""
Test cases for models
"""

from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from core import models


def create_user(email="user@example.com", password="Passw0rd!"):
    """Create and return a sample user"""
    return get_user_model().objects.create_user(email, password)


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

    def test_create_tag(self):
        """
        Test creating a new tag successfully
        """
        user = create_user()
        tag = models.Tag.objects.create(user=user, name="Vegan")
        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """
        Test creating a new ingredient successfully
        """
        user = create_user()
        ingredient = models.Ingredient.objects.create(user=user, name="Cucumber")
        self.assertEqual(str(ingredient), ingredient.name)

    # We use the patch decorator from unittest.mock to replace the uuid.uuid4 method with a mock object.
    # This is done to control the output of uuid.uuid4 during the test, ensuring it returns a predictable value.
    @patch("core.models.uuid.uuid4")
    def test_recipe_file_name_uuid(self, mock_uuid):
        """
        Test that image is saved in the correct location
        """
        # We define a specific UUID string that we want to return when uuid.uuid4() is called in our test.
        uuid = "test-uuid"

        # Here we set what the mock object, mock_uuid, should return when it is called.
        # Instead of generating a new, random UUID, it will return 'test-uuid'.
        mock_uuid.return_value = uuid

        # Call the function that uses uuid.uuid4(). Because we've patched uuid.uuid4, it will use mock_uuid instead,
        # which we've configured to return 'test-uuid'.
        file_path = models.recipe_image_file_path(None, "myimage.jpg")

        # We construct the expected file path string manually using the UUID we provided.
        exp_path = f"uploads/recipe/{uuid}.jpg"

        # The assertion checks if the function returns the path we expect.
        # Since mock_uuid makes uuid.uuid4() return 'test-uuid', the file_path should end up being
        # 'uploads/recipe/test-uuid.jpg', which matches exp_path.
        self.assertEqual(file_path, exp_path)
