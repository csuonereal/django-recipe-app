"""
Views for the recipe APIs
"""

from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Recipe, Tag, Ingredient
from recipe import serializers


class RecipeViewSet(viewsets.ModelViewSet):
    """Manage recipes in the database"""

    serializer_class = serializers.RecipeDetailSerializer
    # we want to get all the recipes, queryset represents the objects that we want to manage
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Return recipes for the current authenticated user only"""
        return self.queryset.filter(user=self.request.user).order_by("-id")

    # it overrides the perform_create function of the ModelViewSet class to set the user of the recipe to the authenticated user
    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)

    # this function is called every time a request is made to the viewset
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == "list":
            return serializers.RecipeSerializer

        return self.serializer_class


# define mixins before generic viewset because we are using mixins in the generic viewset
# we dont want it to be created we want it to be created via the recipe viewset so did not added mixins.CreateModelMixin
class BaseRecipeAttrViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Base viewset for user owned recipe attributes"""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        return self.queryset.filter(user=self.request.user).order_by("-name")


class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags in the database"""

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()

    def get_queryset(self):
        """Return tags for the current authenticated user only"""
        return self.queryset.filter(user=self.request.user).order_by("-name")


class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients in the database"""

    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()


# Key Points:
# 1. Use of GenericViewSet and Mixins:
#    - GenericViewSet alone does not provide any actions. It needs to be combined with mixins to specify which actions are available.
#    - Mixins.ListModelMixin is used here to provide the list action, which is the ability to retrieve all instances of a model (in this case, tags).
#    - This approach is beneficial when you want to provide only a specific set of CRUD operations (like only listing and creating tags) rather than the full set that ModelViewSet offers.

# 2. Why Not ModelViewSet for Tags:
#    - If the requirements for the Tag entity do not include the need for full CRUD operations directly accessible via the API (e.g., updating or deleting tags might not be desired features), using GenericViewSet with specific mixins simplifies the API and reduces potential for unwanted operations.
#    - This approach also allows for cleaner, more controlled exposure of model operations via the API, enhancing security and adherence to the principle of least privilege.

# 3. By choosing GenericViewSet and combining it with appropriate mixins, you tailor the API's capabilities to match exactly what's needed for the Tag model, avoiding the exposure of unnecessary or unwanted CRUD functionality. This method provides a minimalist and secure approach to API design.
