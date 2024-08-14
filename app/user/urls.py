"""
Urls mapping for user API
"""

from django.urls import path
from .views import CreateUserView, CreateTokenView

app_name = "user"  # for reverse mapping

urlpatterns = [
    path("create/", CreateUserView.as_view(), name="create"),
    path("token/", CreateTokenView.as_view(), name="token"),
]
