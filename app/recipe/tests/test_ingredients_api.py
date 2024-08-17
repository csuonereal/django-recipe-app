"""
Tests for the ingredients API
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer
from decimal import Decimal

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def detail_url(ingredient_id):
    """Return ingredient detail URL"""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


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

    def test_update_ingredient(self):
        """Test updating an ingredient"""
        ingredient = create_ingredient(user=self.user, name="Vinegar")
        payload = {"name": "Apple Cider Vinegar"}
        url = detail_url(ingredient.id)
        self.client.patch(url, payload)

        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        """Test deleting an ingredient"""
        ingredient = create_ingredient(user=self.user, name="Vinegar")
        url = detail_url(ingredient.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        exists = Ingredient.objects.filter(
            user=self.user, name=ingredient.name
        ).exists()
        self.assertFalse(exists)

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test filtering ingredients by those assigned to recipes"""
        ingredient_apples = create_ingredient(user=self.user, name="Apples")
        ingredient_turkey = create_ingredient(user=self.user, name="Turkey")
        recipe = Recipe.objects.create(
            user=self.user,
            title="Apple crumble",
            time_minutes=10,
            price=Decimal("5.00"),
            description="Delicious",
            link="https://www.example.com",
        )
        recipe.ingredients.add(ingredient_apples)
        # get only assigned ingredients
        response = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer1 = IngredientSerializer(ingredient_apples)
        serializer2 = IngredientSerializer(ingredient_turkey)

        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_filter_assigned_unique(self):
        """Test filtering ingredients by assigned returns unique items"""
        ingredient = create_ingredient(user=self.user, name="Eggs")
        create_ingredient(user=self.user, name="Cheese")
        recipe1 = Recipe.objects.create(
            user=self.user,
            title="Scrambled eggs",
            time_minutes=5,
            price=Decimal("3.00"),
            description="Simple and tasty",
            link="https://www.example.com",
        )
        recipe1.ingredients.add(ingredient)
        recipe2 = Recipe.objects.create(
            user=self.user,
            title="Egg sandwich",
            time_minutes=10,
            price=Decimal("5.00"),
            description="Simple and tasty",
            link="https://www.example.com",
        )
        recipe2.ingredients.add(ingredient)

        response = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
