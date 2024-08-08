"""
Tests for the user api
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")  # urls in user app and the name of the url
TOKEN_URL = reverse("user:token")


def create_user(**params):  # any dictionary of parameters
    """Create and return a sample user"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()
        self.regular_user_payload = {
            "email": "test@example.com",
            "password": "Passw0rd!",
            "name": "Test User",
        }

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        res = self.client.post(CREATE_USER_URL, self.regular_user_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(self.regular_user_payload["password"]))
        self.assertNotIn(
            "password", res.data
        )  # make sure password is not returned in the response

    def test_user_email_exists_error(self):
        """Test creating a user that already exists fails"""
        create_user(**self.regular_user_payload)

        res = self.client.post(CREATE_USER_URL, self.regular_user_payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that the password must be more than 5 characters"""
        self.regular_user_payload["password"] = "pw"
        res = self.client.post(CREATE_USER_URL, self.regular_user_payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = (
            get_user_model()
            .objects.filter(email=self.regular_user_payload["email"])
            .exists()
        )
        self.assertFalse(user_exists)
        self.regular_user_payload["password"] = "Passw0rd!"  # reset the password

    def test_create_token_for_user(self):
        """Test that a token is created for the user"""
        create_user(**self.regular_user_payload)
        res = self.client.post(TOKEN_URL, self.regular_user_payload)
        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test that token is not created if invalid credentials are given"""
        create_user(**self.regular_user_payload)
        self.regular_user_payload["password"] = "wrong"
        res = self.client.post(TOKEN_URL, self.regular_user_payload)
        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.regular_user_payload["password"] = "Passw0rd!"  # reset the password

    def test_create_token_blank_password(self):
        """Test that token is not created if password is blank"""
        self.regular_user_payload["password"] = ""
        res = self.client.post(TOKEN_URL, self.regular_user_payload)
        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.regular_user_payload["password"] = "Passw0rd!"

    def test_create_token_no_user(self):
        """Test that token is not created if user does not exist"""
        res = self.client.post(TOKEN_URL, self.regular_user_payload)
        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Test that email and password are required"""
        res = self.client.post(TOKEN_URL, {"email": "one", "password": ""})
        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
