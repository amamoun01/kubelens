"""Urls."""

from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_home, name="home"),
    path(
        "logs/<str:namespace>/<str:pod_name>/", views.pod_logs_partial, name="pod_logs"
    ),
]
