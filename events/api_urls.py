from django.urls import path

from . import views

app_name = "events_api"

urlpatterns = [
    path("public/", views.public_feed, name="public"),
    path("private/", views.private_feed, name="private"),
]
