"""Core presentation and operational views."""

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from events.dates import GREGORIAN_MONTHS_EN
from events.forms import HistoricalEventForm
from events.models import Category, HistoricalEvent, Tag


def landing(request: HttpRequest) -> HttpResponse:
    return render(request, "core/landing.html")


def public_timeline(request: HttpRequest) -> HttpResponse:
    context = timeline_context(request)
    context["public_feed_url"] = "/api/events/public/"
    return render(
        request,
        "core/public_timeline.html",
        context,
    )


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    context = timeline_context(request)
    owned = HistoricalEvent.objects.owned_by(request.user)
    context.update({
        "private_feed_url": "/api/events/private/",
        "event_stats": {
            "total": owned.count(),
            "published": owned.filter(is_published=True).count(),
            "private": owned.filter(is_published=False).count(),
        },
        "event_form": HistoricalEventForm(user=request.user),
        "month_choices": tuple(enumerate(GREGORIAN_MONTHS_EN, 1)),
    })
    return render(
        request,
        "core/dashboard.html",
        context,
    )


def timeline_context(request):
    return {
        "categories": Category.objects.order_by("name"),
        "tags": Tag.objects.order_by("name"),
        "selected_tags": request.GET.getlist("tag"),
        "filters": request.GET,
        "era_choices": (("", "All"), ("BCE", "BCE"), ("CE", "CE")),
    }


def database_is_ready() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return False
    return True


def health(request: HttpRequest) -> JsonResponse:
    if not database_is_ready():
        return JsonResponse({"status": "unavailable", "database": "unavailable"}, status=503)
    return JsonResponse({"status": "ok", "database": "ok"})


def live(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


def permission_denied(request: HttpRequest, exception: Exception) -> HttpResponse:
    return render(request, "403.html", status=403)


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    return render(request, "404.html", status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    return render(request, "500.html", status=500)
