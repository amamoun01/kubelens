"""URL configuration for kubelens project."""

from django.urls import path, include

urlpatterns = [
    path("", include("dashboard.urls")),
]
