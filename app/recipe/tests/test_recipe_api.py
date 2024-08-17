"""
Tests for the recipe API
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

# GET /recipes/ mapped to recipe:recipe-list for listing recipes or creating a new one.
# POST /recipes/ also mapped to recipe:recipe-list for creating a new recipe.
# GET /recipes/{id}/ mapped to recipe:recipe-detail for retrieving a recipe.
# PUT /recipes/{id}/ and PATCH /recipes/{id}/ mapped to recipe:recipe-detail for updating a recipe.
# DELETE /recipes/{id}/ mapped to recipe:recipe-detail for deleting a recipe.
# detail_url = reverse('recipe:recipe-detail', kwargs={'pk': recipe_id})
# pk is the primary key of the recipe object
RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


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


def create_user(**params):
    """Create and return a sample user"""
    return get_user_model().objects.create_user(**params)


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
        self.user = create_user(email="user@example.com", password="Passw0rd!")
        # self.user = get_user_model().objects.create_user(
        #     "test@example.com", "Passw0rd!"
        # )
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
        # other_user = get_user_model().objects.create_user(
        #     "otheruser@example.com", "Passw0rd!"
        # )
        other_user = create_user(email="other@example.com", password="Passw0rd!")
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)  # we only created one recipe for the user
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            "title": "Chocolate cheesecake",
            "time_minutes": 30,
            "price": Decimal("5.00"),
            "description": "Sample description",
            "link": "https://samplelink.com",
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))
            # self.assertEqual(payload[key], recipe[key])
            # model instances do not support dictionary-style key access by default.
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        recipe = create_recipe(user=self.user)
        new_title = "Chicken tikka"
        payload = {"title": new_title}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, new_title)
        self.assertEqual(self.user, recipe.user)

    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        recipe = create_recipe(user=self.user)
        payload = {
            "title": "Spaghetti carbonara",
            "time_minutes": 17,
            "price": Decimal("5.30"),
            "description": "Sample description V2",
            "link": "https://samplelinkV2.com",
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))
        self.assertEqual(self.user, recipe.user)

    def test_update_user_returns_error(self):
        """Test that updating the user field returns an error"""
        new_user = create_user(email="new_user@example.com", password="Passw0rd!")
        recipe = create_recipe(user=self.user)
        payload = {"user": new_user.id}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(self.user, recipe.user)
        self.assertNotEqual(new_user, recipe.user)

    def test_deleting_recipe(self):
        """Test deleting a recipe"""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self):
        """Test that a user cannot delete another user's recipe"""
        other_user = create_user(email="otheruser@example.com", password="Passw0rd!")
        recipe = create_recipe(user=other_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        payload = {
            "title": "Avocado lime cheesecake",
            "time_minutes": 60,
            "price": Decimal("20.00"),
            "description": "Sample description",
            "link": "https://samplelink.com",
            "tags": [{"name": "Vegan"}, {"name": "Dessert"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            exists = recipe.tags.filter(name=tag["name"], user=self.user).exists()
            self.assertTrue(exists)

    def create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags"""
        tag1 = Tag.objects.create(user=self.user, name="Vegan")
        payload = {
            "title": "Avocado lime cheesecake",
            "time_minutes": 60,
            "price": Decimal("20.00"),
            "description": "Sample description",
            "link": "https://samplelink.com",
            "tags": [{"name": tag1.name}, {"name": "Breakfast"}],
        }
        # we would expect one tag to be created and the other to be used
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag1, recipe.tags.all())
        for tag in payload["tags"]:
            exists = recipe.tags.filter(name=tag["name"], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating a tag on recipe update"""
        recipe = create_recipe(user=self.user)
        payload = {
            "title": "Avocado lime cheesecake",
            "tags": [{"name": "Vegan"}],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Using .filter() to retrieve tags named "Vegan" for a specific user
        # This line returns a QuerySet, not a single Tag instance. A QuerySet is like a list of all tags that match the criteria,
        # which means it could potentially contain multiple tags or no tags at all.

        # Common misunderstandings when using .filter() instead of .get():
        # 1. A QuerySet is not an actual Tag object but a collection of Tag objects that need to be iterated over or further processed.
        # 2. You cannot directly use 'new_tag' in contexts that require a single object instance, such as assigning to a ForeignKey field,
        #    using in a direct comparison, or asserting existence in a test.

        # Example of incorrect usage that may lead to errors:
        # self.assertIn(new_tag, some_other_queryset)  # This will raise an error because 'new_tag' is a QuerySet, not a single object.
        # new_tag = Tag.objects.filter(name="Vegan", user=self.user)[0] this would solve the issue but lets use get instead
        new_tag = Tag.objects.get(name="Vegan", user=self.user)
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tags(self):
        """Test assigning an existing tag when updating a recipe"""
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)
        tag_dessert = Tag.objects.create(user=self.user, name="Dessert")
        payload = {
            "tags": [{"name": tag_dessert.name}],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.tags.count(), 1)
        self.assertIn(tag_dessert, recipe.tags.all())
        self.assertIn(tag_breakfast, Tag.objects.all())

    def test_clear_recipe_tags(self):
        """Test clearing all tags from a recipe"""
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)
        payload = {
            "tags": [],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.tags.count(), 0)
        self.assertIn(tag_breakfast, Tag.objects.all())

    def test_create_recipe_with_new_ingrediets(self):
        """Test creating recipe with new ingredients"""
        payload = {
            "title": "Chocolate cheesecake",
            "time_minutes": 30,
            "price": Decimal("5.00"),
            "description": "Sample description",
            "link": "https://samplelink.com",
            "ingredients": [{"name": "Chocolate"}, {"name": "Cheese"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user).first()
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """Test creating recipe with existing ingredients"""
        ingredient = Ingredient.objects.create(user=self.user, name="Chocolate")
        payload = {
            "title": "Chocolate cheesecake",
            "time_minutes": 30,
            "price": Decimal("5.00"),
            "description": "Sample description",
            "link": "https://samplelink.com",
            "ingredients": [{"name": "Chocolate"}, {"name": "Cheese"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user).first()
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_ingrediets_on_update(self):
        """Test creating ingredients on recipe update"""
        recipe = create_recipe(user=self.user)
        payload = {
            "title": "Chocolate cheesecake",
            "ingredients": [{"name": "Chocolate"}, {"name": "Cheese"}],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient_chocolate = Ingredient.objects.get(name="Chocolate", user=self.user)
        ingredient_cheese = Ingredient.objects.get(name="Cheese", user=self.user)
        self.assertIn(ingredient_chocolate, recipe.ingredients.all())
        self.assertIn(ingredient_cheese, recipe.ingredients.all())

    def test_update_recipe_assign_ingrediets(self):
        """Test assigning an existing ingredient when updating a recipe"""
        ingredient_chocolate = Ingredient.objects.create(
            user=self.user, name="Chocolate"
        )
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_chocolate)
        ingredient_cheese = Ingredient.objects.create(user=self.user, name="Cheese")
        payload = {
            "ingredients": [{"name": ingredient_cheese.name}],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.ingredients.count(), 1)
        self.assertIn(ingredient_cheese, recipe.ingredients.all())
        self.assertIn(ingredient_chocolate, Ingredient.objects.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing all ingredients from a recipe"""
        ingredient_chocolate = Ingredient.objects.create(
            user=self.user, name="Chocolate"
        )
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_chocolate)
        payload = {
            "ingredients": [],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.ingredients.count(), 0)
        self.assertIn(ingredient_chocolate, Ingredient.objects.all())
