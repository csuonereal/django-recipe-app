"""
Database models
"""

import uuid
import os
from django.db import models

# AbstractBaseUser is a class that implements the core of the user model
# PermissionsMixin is a class that adds the necessary fields and methods to support Django's permission system
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.conf import settings


def recipe_image_file_path(instance, filename):
    """Generate file path for new recipe image"""
    ext = filename.split(".")[-1]  # -1 means the last element of the list
    filename = f"{uuid.uuid4()}.{ext}"

    return os.path.join("uploads/recipe/", filename)  # its base url is MEDIA_ROOT
    # return os.path.join("upload", "recipe", filename) #its base url is MEDIA_ROOT


class UserManager(BaseUserManager):
    """Manager for users"""

    # functions name should be same like below because they are defined in BaseUserManager and we are overriding them
    # we override the create_user and create_superuser function to create a user with an email instead of a username

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a new user"""
        if not email:
            raise ValueError("Users must have an email address")
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

    USERNAME_FIELD = "email"


class Recipe(models.Model):
    """Recipe object"""

    # one user can have multiple recipes but one recipe can only have one user
    # AUTH_USER_MODEL is the user model that is active in the project
    # CASCADE means if the user is deleted, all the recipes associated with that user will also be deleted
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)
    tags = models.ManyToManyField("Tag")
    ingredients = models.ManyToManyField("Ingredient")
    # we are passing the function reference, not calling the function
    image = models.ImageField(null=True, upload_to=recipe_image_file_path)

    def __str__(self):
        return self.title


class Tag(models.Model):
    """Tag to be used for a recipe to help in filtering"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ingredient to be used in a recipe"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
