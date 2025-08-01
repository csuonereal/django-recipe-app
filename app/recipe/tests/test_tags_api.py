"""
Test cases for tags API
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Tag, Recipe
from recipe.serializers import TagSerializer

TAGS_URL = reverse("recipe:tag-list")


def detail_url(tag_id):
    """Return tag detail URL"""
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email="user@example.com", password="Passw0rd!"):
    """Create and return a sample user"""
    return get_user_model().objects.create_user(email, password)


def create_tags(user, name):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


class PublicTagsApiTests(TestCase):
    """Test the publicly available tags API"""

    def setUp(self):
        """Set up the client for each test"""
        self.client = APIClient()

    def tearDown(self):
        """Clean up any created tags and users after each test"""
        Tag.objects.all().delete()
        get_user_model().objects.all().delete()

    def test_login_required(self):
        """Test that login is required for retrieving tags"""
        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test the authorized user tags API"""

    def setUp(self):
        """Set up the client for each test"""
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def tearDown(self):
        """Clean up any created tags and users after each test"""
        Tag.objects.all().delete()
        get_user_model().objects.all().delete()

    def test_retrieve_tags(self):
        """Test retrieving tags"""

        create_tags(user=self.user, name="Breakfast")
        create_tags(user=self.user, name="Lunch")

        response = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are for the authenticated user"""
        user2 = create_user(email="user2@example.com", password="Passw0rd!")
        create_tags(user=user2, name="Dinner")
        tag = create_tags(user=self.user, name="Dessert")

        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], tag.name)

    def test_update_tag(self):
        """Test updating a tag"""
        tag = create_tags(user=self.user, name="Breakfast")
        payload = {"name": "Brunch"}
        url = detail_url(tag.id)
        self.client.patch(url, payload)

        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        """Test deleting a tag"""
        tag = create_tags(user=self.user, name="Breakfast")
        url = detail_url(tag.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test filtering tags by those assigned to recipes"""
        tag1 = create_tags(user=self.user, name="Breakfast")
        tag2 = create_tags(user=self.user, name="Lunch")
        recipe = Recipe.objects.create(
            title="Coriander eggs on toast",
            time_minutes=10,
            price=Decimal("5.00"),
            user=self.user,
        )
        recipe.tags.add(tag1)

        response = self.client.get(
            TAGS_URL,
            {"assigned_only": 1},
        )

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_filter_tags_assigned_unique(self):
        """Test filtering tags by assigned returns unique items"""
        tag = create_tags(user=self.user, name="Breakfast")
        create_tags(user=self.user, name="Lunch")
        recipe1 = Recipe.objects.create(
            title="Pancakes",
            time_minutes=5,
            price=Decimal("3.00"),
            user=self.user,
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            title="Porridge",
            time_minutes=3,
            price=Decimal("2.00"),
            user=self.user,
        )
        recipe2.tags.add(tag)

        response = self.client.get(
            TAGS_URL,
            {"assigned_only": 1},
        )

        self.assertEqual(len(response.data), 1)
