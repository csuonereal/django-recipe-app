"""
Database models
"""

from django.db import models
# AbstractBaseUser is a class that implements the core of the user model
# PermissionsMixin is a class that adds the necessary fields and methods to support Django's permission system
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
    PermissionsMixin


class UserManager(BaseUserManager):
    """Manager for users"""

    # functions name should be same like below because they are defined in BaseUserManager and we are overriding them
    # we override the create_user and create_superuser function to create a user with an email instead of a username

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a new user"""
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and return a new superuser"""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system"""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
