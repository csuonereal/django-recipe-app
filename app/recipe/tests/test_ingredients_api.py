"""
Tests for the ingredients API
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def create_user(email="user@example.com", password="Passw0rd!"):
    """Create and return a sample user"""
    return get_user_model().objects.create_user(email, password)


def create_ingredient(user, name):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


class PublicIngredientsApiTests(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self):
        """Set up the client for each test"""
        self.client = APIClient()

    def tearDown(self):
        """Clean up any created ingredients and users after each test"""
        Ingredient.objects.all().delete()
        get_user_model().objects.all().delete()

    def test_login_required(self):
        """Test that login is required for retrieving ingredients"""
        response = self.client.get(INGREDIENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test the authorized user ingredients API"""

    def setUp(self):
        """Set up the client for each test"""
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def tearDown(self):
        """Clean up any created ingredients and users after each test"""
        Ingredient.objects.all().delete()
        get_user_model().objects.all().delete()

    def test_retrieve_ingredients_list(self):
        """Test retrieving a list of ingredients"""
        create_ingredient(user=self.user, name="Kale")
        create_ingredient(user=self.user, name="Salt")

        response = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test that ingredients for the authenticated user are returned"""
        user2 = create_user(email="user2@example.com")
        create_ingredient(user=user2, name="Vinegar")
        ingredient = create_ingredient(user=self.user, name="Tumeric")

        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], ingredient.name)
        self.assertEqual(response.data[0]["id"], ingredient.id)
