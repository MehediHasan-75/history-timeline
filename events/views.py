from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .dates import GREGORIAN_MONTHS_EN
from .forms import HistoricalEventForm
from .models import HistoricalEvent
from .serializers import serialize_event
from .services import FilterError, filter_events


def _form_context(form, event=None):
    return {"form": form, "event": event, "month_choices": tuple(enumerate(GREGORIAN_MONTHS_EN, 1))}


@login_required
def event_list(request: HttpRequest) -> HttpResponse:
    try:
        events = filter_events(HistoricalEvent.objects.owned_by(request.user).select_related("category"), request.GET)
    except FilterError as exc:
        messages.error(request, str(exc))
        events = HistoricalEvent.objects.none()
    page = Paginator(events, 20).get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    return render(request, "events/event_list.html", {"events": page.object_list, "page_obj": page, "pagination_query": query.urlencode()})


def event_detail(request: HttpRequest, pk: int) -> HttpResponse:
    event = get_object_or_404(
        HistoricalEvent.objects.visible_to(request.user).select_related("category", "owner").prefetch_related("tags"), pk=pk
    )
    return render(request, "events/event_detail.html", {"event": event})


@login_required
@require_http_methods(["GET", "POST"])
def event_create(request: HttpRequest) -> HttpResponse:
    form = HistoricalEventForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        event = form.save()
        messages.success(request, "Event created.")
        return redirect("events:detail", pk=event.pk)
    return render(request, "events/event_form.html", _form_context(form))


@login_required
@require_http_methods(["GET", "POST"])
def event_edit(request: HttpRequest, pk: int) -> HttpResponse:
    event = get_object_or_404(HistoricalEvent, pk=pk, owner=request.user)
    form = HistoricalEventForm(request.POST or None, instance=event, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Event updated.")
        return redirect("events:detail", pk=event.pk)
    return render(request, "events/event_form.html", _form_context(form, event))


@login_required
@require_http_methods(["GET", "POST"])
def event_delete(request: HttpRequest, pk: int) -> HttpResponse:
    event = get_object_or_404(HistoricalEvent, pk=pk, owner=request.user)
    if request.method == "POST":
        event.delete()
        messages.success(request, "Event deleted.")
        return redirect("events:list")
    return render(request, "events/event_confirm_delete.html", {"event": event})


def _feed(request, queryset):
    try:
        events = filter_events(queryset.select_related("category").prefetch_related("tags"), request.GET)
    except FilterError as exc:
        return JsonResponse({"error": {"code": "invalid_filter", "message": str(exc)}}, status=400)
    return JsonResponse({"scale": "human", "events": [serialize_event(event) for event in events]})


def public_feed(request: HttpRequest) -> JsonResponse:
    return _feed(request, HistoricalEvent.objects.published())


@login_required
def private_feed(request: HttpRequest) -> JsonResponse:
    return _feed(request, HistoricalEvent.objects.owned_by(request.user))
