from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .dates import BENGALI_BD, GREGORIAN, DatePoint, calendar_bounds, normalize_digits
from .forms import HistoricalEventForm
from .models import Category, HistoricalEvent


class BengaliCalendarTests(SimpleTestCase):
    def test_1370_maps_to_1963_1964(self):
        bounds = calendar_bounds(BENGALI_BD, 1370)
        self.assertEqual(bounds.lower, DatePoint(1963, 4, 14))
        self.assertEqual(bounds.upper, DatePoint(1964, 4, 13))

    def test_bengali_digits_normalize(self):
        self.assertEqual(normalize_digits("১৩৭০"), "1370")

    def test_gregorian_bce_bounds_and_year_zero(self):
        self.assertEqual(calendar_bounds(GREGORIAN, -44, 3, 15).lower, DatePoint(-44, 3, 15))
        with self.assertRaisesMessage(Exception, "year zero"):
            calendar_bounds(GREGORIAN, 0)


class EventFlowTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user("owner", password="test-password-123")
        self.other = get_user_model().objects.create_user("other", password="test-password-123")
        self.category = Category.objects.create(name="বাংলা ইতিহাস")

    def form_data(self, **overrides):
        data = {
            "title": "১৩৭০ / 1963",
            "description": "বাংলা and English",
            "category": self.category.pk,
            "start_calendar": BENGALI_BD,
            "start_year_abs": "১৩৭০",
            "start_month": "",
            "start_day": "",
            "end_calendar": GREGORIAN,
            "end_year_abs": "",
            "end_month": "",
            "end_day": "",
        }
        data.update(overrides)
        return data

    def test_form_accepts_bengali_digits_and_persists_bounds(self):
        form = HistoricalEventForm(self.form_data(), user=self.owner)
        self.assertTrue(form.is_valid(), form.errors)
        event = form.save()
        self.assertEqual((event.start_lower_year, event.start_lower_month, event.start_lower_day), (1963, 4, 14))
        self.assertEqual((event.start_upper_year, event.start_upper_month, event.start_upper_day), (1964, 4, 13))

    def test_private_event_permissions_and_public_feed(self):
        event = HistoricalEvent.objects.create(
            owner=self.owner, category=self.category, title="Private", description="Secret",
            start_calendar=GREGORIAN, start_year=1971,
        )
        self.assertEqual(self.client.get(reverse("events:detail", args=[event.pk])).status_code, 404)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("events:detail", args=[event.pk])).status_code, 404)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("events:detail", args=[event.pk])).status_code, 200)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("events_api:public")).json()["events"], [])

    def test_published_bengali_event_serializes_converted_span(self):
        event = HistoricalEvent.objects.create(
            owner=self.owner, category=self.category, title="<script>alert(1)</script>", description="নিরাপদ",
            start_calendar=BENGALI_BD, start_year=1370, is_published=True,
        )
        payload = self.client.get(reverse("events_api:public")).json()["events"][0]
        self.assertEqual(payload["start_date"]["year"], 1963)
        self.assertEqual(payload["end_date"]["year"], 1964)
        self.assertIn("&lt;script&gt;", payload["text"]["headline"])

    def test_bengali_year_filter_overlaps_both_gregorian_years(self):
        HistoricalEvent.objects.create(
            owner=self.owner, category=self.category, title="1370", description="Year",
            start_calendar=BENGALI_BD, start_year=1370, is_published=True,
        )
        response = self.client.get(reverse("events_api:public"), {"calendar": BENGALI_BD, "year_from": "১৩৭০", "year_to": "১৩৭০"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["events"]), 1)

    def test_invalid_filter_returns_structured_400(self):
        response = self.client.get(reverse("events_api:public"), {"calendar": BENGALI_BD, "era": "BCE"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_filter")
