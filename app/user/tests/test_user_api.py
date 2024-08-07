"""
Tests for the user api
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")  # urls in user app and the name of the url
#TOKEN_URL = reverse("user:token")


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
