"""
Tests for the recipe API
"""

import tempfile
import os
from PIL import Image
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


def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])
    # action: upload_image


def detail_url(recipe_id):
    """Return recipe detail URL"""
    # it's a pre defined action in the RecipeViewSet
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

    def test_filter_recipes_by_tags(self):
        """Test returning recipes with specific tags"""
        recipe1 = create_recipe(user=self.user, title="Thai vegetable curry")
        recipe2 = create_recipe(user=self.user, title="Aubergine with tahini")
        recipe3 = create_recipe(user=self.user, title="Fish and chips")
        tag1 = Tag.objects.create(user=self.user, name="Vegan")
        tag2 = Tag.objects.create(user=self.user, name="Vegetarian")
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        url = RECIPES_URL + "?tags=" + f"{tag1.id},{tag2.id}"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """Test returning recipes with specific ingredients"""
        recipe1 = create_recipe(user=self.user, title="Posh beans on toast")
        recipe2 = create_recipe(user=self.user, title="Chicken cacciatore")
        recipe3 = create_recipe(user=self.user, title="Steak and mushrooms")
        ingredient1 = Ingredient.objects.create(user=self.user, name="Feta cheese")
        ingredient2 = Ingredient.objects.create(user=self.user, name="Chicken")
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        url = RECIPES_URL + "?ingredients=" + f"{ingredient1.id},{ingredient2.id}"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)


class ImageUploadTests(TestCase):
    """Test image upload functionality"""

    def setUp(self):
        """Set up the client for each test"""
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="Passw0rd!")
        self.client.force_authenticate(user=self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        """Clean up any created users and recipes after each test"""
        self.recipe.image.delete()
        Recipe.objects.all().delete()
        get_user_model().objects.all().delete()

    def test_upload_image_to_recipe(self):
        """Test uploading an image to a recipe"""
        # Obtain the URL for uploading images to a specific recipe, using the recipe's ID.
        # This URL is likely configured to handle POST requests with image data.
        url = image_upload_url(self.recipe.id)

        # Use Python's tempfile.NamedTemporaryFile to create a temporary file on the system.
        # The suffix ".jpg" ensures the file is named with a .jpg extension, mimicking an actual image file.
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            # Create a simple image using PIL (Pillow library). This example creates a black square of 10x10 pixels.
            # This simulates an actual image without needing to use a real image file.
            img = Image.new("RGB", (10, 10))  # 'RGB' for color image, 10x10 pixels.
            img.save(
                image_file, format="JPEG"
            )  # Save the newly created image to the tempfile in JPEG format.

            # Seek to the start of the file. After saving the file, the file's pointer is at the end of the file.
            # We reset it to the beginning so it can be read from the start in the next step.
            image_file.seek(0)

            # Post the image to the server using the image upload URL. We include the image file in the POST data.
            # The 'format="multipart"' argument ensures that the request is treated as a multipart/form-data POST,
            # which is the correct format for file uploads.
            res = self.client.post(url, {"image": image_file}, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)

        # Verify that the image file exists in the location specified by the recipe's image field.
        # This checks if the file was not only uploaded but saved correctly by the server.
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {"image": "notimage"}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
