"""
Urls mappings for recipe app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from recipe import views

router = DefaultRouter()
# first argument is the name of the endpoint / URL
# the first argument is the name of the endpoint, the second argument is the viewset that we want to register
# basically automatically generate the URL patterns for our viewset depending on the actions that we have in our viewset
router.register("recipes", views.RecipeViewSet)

app_name = "recipe"

urlpatterns = [
    path("", include(router.urls)),
]
