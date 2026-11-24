import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils.text import slugify

from .dates import BENGALI_BD, CALENDAR_CHOICES, GREGORIAN, calendar_bounds, format_source_date


def unique_slug(instance, value, max_length):
    base = slugify(value, allow_unicode=True)[:max_length] or "item"
    candidate, number = base, 2
    model = type(instance)
    while model.objects.exclude(pk=instance.pk).filter(slug=candidate).exists():
        suffix = f"-{number}"
        candidate = f"{base[:max_length-len(suffix)]}{suffix}"
        number += 1
    return candidate


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, allow_unicode=True, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#b45309")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", self.color):
            raise ValidationError({"color": "Use a six-digit hexadecimal color such as #b45309."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, 120)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=70, unique=True, allow_unicode=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(Lower("name"), name="events_tag_name_ci_unique")]

    def save(self, *args, **kwargs):
        self.name = " ".join(self.name.split())
        if not self.slug:
            self.slug = unique_slug(self, self.name, 70)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class HistoricalEventQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def owned_by(self, user):
        return self.filter(owner=user)

    def visible_to(self, user):
        return self.filter(models.Q(is_published=True) | models.Q(owner=user)) if user.is_authenticated else self.published()


class HistoricalEvent(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="historical_events")
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="events")
    tags = models.ManyToManyField(Tag, blank=True, related_name="events")
    start_calendar = models.CharField(max_length=20, choices=CALENDAR_CHOICES, default=GREGORIAN)
    start_year = models.IntegerField()
    start_month = models.PositiveSmallIntegerField(null=True, blank=True)
    start_day = models.PositiveSmallIntegerField(null=True, blank=True)
    end_calendar = models.CharField(max_length=20, choices=CALENDAR_CHOICES, default=GREGORIAN)
    end_year = models.IntegerField(null=True, blank=True)
    end_month = models.PositiveSmallIntegerField(null=True, blank=True)
    end_day = models.PositiveSmallIntegerField(null=True, blank=True)
    start_lower_year = models.IntegerField(editable=False)
    start_lower_month = models.PositiveSmallIntegerField(editable=False)
    start_lower_day = models.PositiveSmallIntegerField(editable=False)
    start_upper_year = models.IntegerField(editable=False)
    start_upper_month = models.PositiveSmallIntegerField(editable=False)
    start_upper_day = models.PositiveSmallIntegerField(editable=False)
    end_lower_year = models.IntegerField(null=True, editable=False)
    end_lower_month = models.PositiveSmallIntegerField(null=True, editable=False)
    end_lower_day = models.PositiveSmallIntegerField(null=True, editable=False)
    end_upper_year = models.IntegerField(null=True, editable=False)
    end_upper_month = models.PositiveSmallIntegerField(null=True, editable=False)
    end_upper_day = models.PositiveSmallIntegerField(null=True, editable=False)
    is_published = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = HistoricalEventQuerySet.as_manager()

    class Meta:
        ordering = ("start_lower_year", "start_lower_month", "start_lower_day", "pk")
        constraints = [
            models.CheckConstraint(condition=~models.Q(start_year=0), name="event_start_year_nonzero"),
            models.CheckConstraint(condition=models.Q(start_month__isnull=True) | models.Q(start_month__range=(1, 12)), name="event_start_month_valid"),
            models.CheckConstraint(condition=models.Q(start_day__isnull=True) | models.Q(start_day__range=(1, 31)), name="event_start_day_valid"),
            models.CheckConstraint(condition=models.Q(start_day__isnull=True) | models.Q(start_month__isnull=False), name="event_start_day_requires_month"),
            models.CheckConstraint(condition=models.Q(end_year__isnull=True) | ~models.Q(end_year=0), name="event_end_year_nonzero"),
            models.CheckConstraint(condition=models.Q(end_month__isnull=True) | models.Q(end_month__range=(1, 12)), name="event_end_month_valid"),
            models.CheckConstraint(condition=models.Q(end_day__isnull=True) | models.Q(end_day__range=(1, 31)), name="event_end_day_valid"),
            models.CheckConstraint(condition=models.Q(end_day__isnull=True) | models.Q(end_month__isnull=False), name="event_end_day_requires_month"),
            models.CheckConstraint(condition=models.Q(end_year__isnull=False) | (models.Q(end_month__isnull=True) & models.Q(end_day__isnull=True)), name="event_end_parts_require_year"),
            models.CheckConstraint(condition=~models.Q(start_calendar=BENGALI_BD) | models.Q(start_year__gt=0), name="event_bengali_start_positive"),
            models.CheckConstraint(condition=~models.Q(end_calendar=BENGALI_BD) | models.Q(end_year__isnull=True) | models.Q(end_year__gt=0), name="event_bengali_end_positive"),
        ]
        indexes = [
            models.Index(fields=("owner", "start_lower_year")),
            models.Index(fields=("is_published", "start_lower_year")),
            models.Index(fields=("category", "start_lower_year")),
        ]

    def populate_bounds(self):
        start = calendar_bounds(self.start_calendar, self.start_year, self.start_month, self.start_day)
        for side, point in (("lower", start.lower), ("upper", start.upper)):
            for component in ("year", "month", "day"):
                setattr(self, f"start_{side}_{component}", getattr(point, component))
        if self.end_year is None:
            if self.end_month is not None or self.end_day is not None:
                raise ValidationError("End month and day require an end year.")
            for side in ("lower", "upper"):
                for component in ("year", "month", "day"):
                    setattr(self, f"end_{side}_{component}", None)
            return
        end = calendar_bounds(self.end_calendar, self.end_year, self.end_month, self.end_day)
        if end.upper < start.lower:
            raise ValidationError("End date cannot be earlier than start date.")
        for side, point in (("lower", end.lower), ("upper", end.upper)):
            for component in ("year", "month", "day"):
                setattr(self, f"end_{side}_{component}", getattr(point, component))

    def clean(self):
        self.populate_bounds()

    def save(self, *args, **kwargs):
        self.populate_bounds()
        super().save(*args, **kwargs)

    @property
    def display_date(self):
        start = format_source_date(self.start_calendar, self.start_year, self.start_month, self.start_day)
        if self.end_year is None:
            return start
        end = format_source_date(self.end_calendar, self.end_year, self.end_month, self.end_day)
        return f"{start} – {end}"

    def __str__(self):
        return self.title
