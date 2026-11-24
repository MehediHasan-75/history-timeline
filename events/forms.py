from django import forms
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .dates import BENGALI_BD, CALENDAR_CHOICES, GREGORIAN, normalize_digits
from .models import HistoricalEvent, Tag


class LocalizedIntegerField(forms.IntegerField):
    def to_python(self, value):
        return super().to_python(normalize_digits(value))


class HistoricalEventForm(forms.ModelForm):
    start_calendar = forms.ChoiceField(choices=CALENDAR_CHOICES)
    start_year_abs = LocalizedIntegerField(min_value=1)
    start_era = forms.ChoiceField(choices=(("BCE", "BCE"), ("CE", "CE")), initial="CE", required=False)
    start_month = LocalizedIntegerField(min_value=1, max_value=12, required=False)
    start_day = LocalizedIntegerField(min_value=1, max_value=31, required=False)
    end_calendar = forms.ChoiceField(choices=CALENDAR_CHOICES, required=False, initial=GREGORIAN)
    end_year_abs = LocalizedIntegerField(min_value=1, required=False)
    end_era = forms.ChoiceField(choices=(("BCE", "BCE"), ("CE", "CE")), initial="CE", required=False)
    end_month = LocalizedIntegerField(min_value=1, max_value=12, required=False)
    end_day = LocalizedIntegerField(min_value=1, max_value=31, required=False)
    new_tags = forms.CharField(required=False, max_length=500)

    class Meta:
        model = HistoricalEvent
        fields = ("title", "description", "category", "tags", "is_published")
        widgets = {"tags": forms.CheckboxSelectMultiple}

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["tags"].queryset = Tag.objects.order_by("name")
        if self.instance.pk and not self.is_bound:
            for prefix in ("start", "end"):
                year = getattr(self.instance, f"{prefix}_year")
                calendar = getattr(self.instance, f"{prefix}_calendar")
                if year is not None:
                    self.initial[f"{prefix}_year_abs"] = abs(year)
                    self.initial[f"{prefix}_era"] = "BCE" if calendar == GREGORIAN and year < 0 else "CE"
                self.initial[f"{prefix}_calendar"] = calendar
                self.initial[f"{prefix}_month"] = getattr(self.instance, f"{prefix}_month")
                self.initial[f"{prefix}_day"] = getattr(self.instance, f"{prefix}_day")

    def clean(self):
        cleaned = super().clean()
        for prefix, required in (("start", True), ("end", False)):
            calendar = cleaned.get(f"{prefix}_calendar") or GREGORIAN
            absolute = cleaned.get(f"{prefix}_year_abs")
            if required and absolute is None:
                self.add_error(f"{prefix}_year_abs", "Year is required.")
                continue
            if absolute is None:
                if cleaned.get(f"{prefix}_month") or cleaned.get(f"{prefix}_day"):
                    self.add_error(f"{prefix}_year_abs", "Enter a year before month or day.")
                cleaned[f"{prefix}_year"] = None
                continue
            if calendar == BENGALI_BD:
                year = absolute
            else:
                era = cleaned.get(f"{prefix}_era")
                if era not in ("BCE", "CE"):
                    self.add_error(f"{prefix}_era", "Choose BCE or CE.")
                    continue
                year = -absolute if era == "BCE" else absolute
            cleaned[f"{prefix}_year"] = year

        if not self.errors:
            probe = self.instance
            for prefix in ("start", "end"):
                for component in ("calendar", "year", "month", "day"):
                    value = cleaned.get(f"{prefix}_{component}")
                    if component == "calendar" and not value:
                        value = GREGORIAN
                    setattr(probe, f"{prefix}_{component}", value)
            try:
                probe.populate_bounds()
            except ValidationError as exc:
                raise forms.ValidationError(exc.messages)
        return cleaned

    def save(self, commit=True):
        event = super().save(commit=False)
        for prefix in ("start", "end"):
            for component in ("calendar", "year", "month", "day"):
                value = self.cleaned_data.get(f"{prefix}_{component}")
                if component == "calendar" and not value:
                    value = GREGORIAN
                setattr(event, f"{prefix}_{component}", value)
        if self.user and not event.owner_id:
            event.owner = self.user
        if commit:
            with transaction.atomic():
                event.save()
                self.save_m2m()
                for raw_name in self.cleaned_data.get("new_tags", "").split(","):
                    name = " ".join(raw_name.split())
                    if not name:
                        continue
                    tag = Tag.objects.filter(name__iexact=name).first()
                    if not tag:
                        try:
                            with transaction.atomic():
                                tag = Tag.objects.create(name=name, created_by=self.user)
                        except IntegrityError:
                            tag = Tag.objects.get(name__iexact=name)
                    event.tags.add(tag)
        return event
