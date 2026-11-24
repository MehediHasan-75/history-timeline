from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("timeline/", views.public_timeline, name="public_timeline"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("health/", views.health, name="health"),
    path("health/live/", views.live, name="live"),
    path("health/ready/", views.health, name="ready"),
]
