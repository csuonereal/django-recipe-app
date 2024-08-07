"""
Test for the Django admin modifications
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):
    """Test for Django admin"""

    def setUp(self):
        """Create test client and admin user"""
        admin_user_email = "admin@example.com"
        regular_user_email = "test@example.com"
        regular_user_name = "Test User"
        password = "Passw0rd!"
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email=admin_user_email, password=password
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email=regular_user_email, password=password, name=regular_user_name
        )

    def test_users_list(self):
        """Test that users are listed on user page"""
        url = reverse(
            "admin:core_user_changelist"
        )  # /admin/core/user/ defined in Django admin documentation
        response = self.client.get(url)

        self.assertContains(response, self.user.name)
        self.assertContains(response, self.user.email)

    def test_edit_user_page(self):
        """Test that the user edit page works"""
        url = reverse("admin:core_user_change", args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_user_page(self):
        """Test that the create user page works"""
        url = reverse("admin:core_user_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
