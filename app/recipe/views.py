"""
Views for the recipe APIs
"""

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Recipe, Tag, Ingredient
from recipe import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="tags",
                # actual type of the parameter and later on we convert it to a list of integers
                type=OpenApiTypes.STR,
                description="Comma separated list of tag IDs to filter",
            ),
            OpenApiParameter(
                name="ingredients",
                type=OpenApiTypes.STR,
                description="Comma separated list of ingredient IDs to filter",
            ),
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """Manage recipes in the database"""

    serializer_class = serializers.RecipeDetailSerializer
    # we want to get all the recipes, queryset represents the objects that we want to manage
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def _params_to_ints(self, qs):
        """Convert a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Return recipes for the current authenticated user only"""
        tags = self.request.query_params.get("tags")
        ingredients = self.request.query_params.get("ingredients")
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)
        # we used distinct because you can get duplicate results if you have multiple
        # recipes assigned to the same tag or ingredient
        return queryset.filter(user=self.request.user).order_by("-id").distinct()

    # it overrides the perform_create function of the ModelViewSet class
    # to set the user of the recipe to the authenticated user
    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)

    # this function is called every time a request is made to the viewset
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == "list":
            return serializers.RecipeSerializer
        elif self.action == "upload_image":
            return serializers.RecipeImageSerializer

        return self.serializer_class

    # The @action decorator is used to add custom actions
    # to standard CRUD operations provided by Django REST Framework's viewsets.
    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        """
        Custom action to upload an image to a recipe.

        This endpoint is specifically for uploading images associated with a recipe, extending
        the standard REST actions like list, create, retrieve, update, and delete.
        """
        # The 'detail=True' parameter specifies that this action is to be performed on a specific instance,
        # rather than a whole collection. It therefore requires the recipe's primary key ('pk') to be specified in the URL.

        # 'url_path="upload-image"' determines the URL path that this action will be accessible from.
        # For instance, if the base URL for the RecipeViewSet is '/recipes/',
        # this action will be available at '/recipes/{pk}/upload-image/'.

        # Retrieves the recipe instance by its primary key ('pk') using DRF's built-in method `get_object`,
        # which also checks for permissions and raises a 404 if the object does not exist.
        recipe = self.get_object()

        # Initializes the serializer instance with the retrieved recipe object and the incoming request data.
        # This is intended for validating and deserializing input data to the image field.
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# define mixins before generic viewset because we are using mixins in the generic viewset
# we dont want it to be created we want it to be created via the recipe viewset so did not added mixins.CreateModelMixin


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="assigned_only",
                type=OpenApiTypes.INT,
                enum=[0, 1],
                description="Filter tags by assigned recipes",
            )
        ]
    )
)
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
        assigned_only = bool(int(self.request.query_params.get("assigned_only", 0)))
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        return queryset.filter(user=self.request.user).order_by("-name").distinct()


class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags in the database"""

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


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
