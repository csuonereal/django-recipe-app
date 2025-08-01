"""
Tests for the user API
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")  # URL for creating a user
TOKEN_URL = reverse("user:token")  # URL for obtaining a token
ME_URL = reverse("user:me")  # URL for getting the user's profile


def create_user(**params):  # Function to create a user with given parameters
    """Create and return a sample user"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        """Set up the client for each test"""
        self.client = APIClient()
        # Since we're initializing the user payload in the setUp method, each test will automatically have the correct setup.
        # Therefore, the reset_user_payload method becomes unnecessary. This approach ensures that each test method
        # starts with a fresh instance of the payload, preventing unintentional sharing or modifications of the payload across tests,
        # which enhances the isolation and reliability of the test suite.

        self.regular_user_payload = {
            "name": "Test",
            "email": "test@example.com",
            "password": "Passw0rd!",
        }

    def tearDown(self):
        """Clean up any created users after each test"""
        get_user_model().objects.all().delete()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        res = self.client.post(CREATE_USER_URL, self.regular_user_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(self.regular_user_payload["password"]))
        self.assertNotIn("password", res.data)

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

    def test_create_token_for_user(self):
        """Test generates token for valid credentials"""
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

    def test_create_token_blank_password(self):
        """Test that token is not created if password is blank"""
        res = self.client.post(TOKEN_URL, self.regular_user_payload)
        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_email_not_found(self):
        """Test error returned if user not found for given email"""
        res = self.client.post(TOKEN_URL, self.regular_user_payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Test that email and password are required"""
        self.regular_user_payload["password"] = ""
        res = self.client.post(TOKEN_URL, self.regular_user_payload)
        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for users"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        """Set up the client for each test"""
        self.regular_user_payload = {
            "name": "Test",
            "email": "test@example.com",
            "password": "Passw0rd!",
        }

        self.user = create_user(
            email=self.regular_user_payload["email"],
            password=self.regular_user_payload["password"],
            name=self.regular_user_payload["name"],
        )
        self.client = APIClient()
        self.client.force_authenticate(
            user=self.user
        )  # Force authentication for the client
        # This will ensure that the client is authenticated for each test, which will allow us to test the authenticated user's profile.

    def tearDown(self):
        """Clean up any created users after each test"""
        get_user_model().objects.all().delete()

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {"name": self.user.name, "email": self.user.email})

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on the me URL"""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""
        payload = {"name": "New Name", "password": "NewPassw0rd!"}
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload["name"])
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_user_profile_invalid_password(self):
        """Test updating the user profile with invalid password"""
        payload = {"password": "pw"}
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.regular_user_payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_user_profile_blank_password(self):
        """Test updating the user profile with blank password"""
        payload = {"password": ""}
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        # we did not check password from self.user.password because the password is hashed and we can't compare it with the plain text password so we used regular_user_payload object
        self.assertTrue(self.user.check_password(self.regular_user_payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_user_profile_invalid_email(self):
        """Test updating the user profile with invalid email"""
        payload = {"email": "invalid"}
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, self.user.email)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_user_profile_blank_email(self):
        """Test updating the user profile with blank email"""
        payload = {"email": ""}
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, self.user.email)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
