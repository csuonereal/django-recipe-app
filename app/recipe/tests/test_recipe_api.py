"""
Tests for the recipe API
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe
from recipe.serializers import RecipeSerializer

# GET /recipes/ mapped to recipe:recipe-list for listing recipes or creating a new one.
# POST /recipes/ also mapped to recipe:recipe-list for creating a new recipe.
# GET /recipes/{id}/ mapped to recipe:recipe-detail for retrieving a recipe.
# PUT /recipes/{id}/ and PATCH /recipes/{id}/ mapped to recipe:recipe-detail for updating a recipe.
# DELETE /recipes/{id}/ mapped to recipe:recipe-detail for deleting a recipe.
# detail_url = reverse('recipe:recipe-detail', kwargs={'pk': recipe_id})
# pk is the primary key of the recipe object
RECIPES_URL = reverse("recipe:recipe-list")


def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        "title": "Sample recipe",
        "time_minutes": 10,
        "price": Decimal("5.00"),
        "description": "Sample description",
        "link": "https://samplelink.com",
    }
    defaults.update(
        params
    )  # update the defaults with the params if we dont send the params, it will use the defaults
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self):
        """Set up the client for each test"""
        self.client = APIClient()

    def tearDown(self):
        """Clean up any created users and recipes after each test"""
        Recipe.objects.all().delete()
        get_user_model().objects.all().delete()

    def test_auth_required(self):
        """Test that authentication is required"""
        res = self.client.get(
            RECIPES_URL
        )  # try to get the recipes without authentication
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe API access"""

    def setUp(self):
        """Set up the client for each test"""
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@example.com", "Passw0rd!"
        )
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        """Clean up any created users and recipes after each test"""
        Recipe.objects.all().delete()
        get_user_model().objects.all().delete()

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        # many=True because we are serializing a queryset which means we are serializing multiple objects
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # compare the response data with the serializer data
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for user"""
        other_user = get_user_model().objects.create_user(
            "otheruser@example.com", "Passw0rd!"
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)  # we only created one recipe for the user
        self.assertEqual(res.data, serializer.data)
