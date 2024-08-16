"""
Django admin configuration
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from core import models
from django.utils.translation import (
    gettext_lazy as _,
)  # This is used to translate strings to the user's language


class UserAdmin(BaseUserAdmin):
    """Define custom user model for Django admin"""

    ordering = ["id"]
    list_display = ["email", "name"]
    # Define the sections that appear on the change and create pages
    fieldsets = (  # This is the configuration for the update user page
        (None, {"fields": ("email", "password")}),  # None is the title of the section
        (_("Personal Info"), {"fields": ("name",)}),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser")},
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )
    readonly_fields = ("last_login",)  # This field is read-only can't be edited
    add_fieldsets = (  # This is the configuration for the create user page
        (
            None,
            {
                "classes": (
                    "wide",
                ),  # This is the CSS class that is applied to the fieldset
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "name",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


# we dont need to give custom admin class for Recipe model because it aleady has
admin.site.register(models.Recipe)
admin.site.register(models.Tag)
admin.site.register(models.User, UserAdmin)
