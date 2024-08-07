"""
Urls mapping for user API
"""

from django.urls import path
from .views import CreateUserView

app_name = "user"  # for reverse mapping

urlpatterns = [
    path("create/", CreateUserView.as_view(), name="create"),
]
