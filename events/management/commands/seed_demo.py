from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from events.dates import BENGALI_BD, GREGORIAN
from events.models import Category, HistoricalEvent, Tag


class Command(BaseCommand):
    help = "Create deterministic bilingual demonstration data."

    def handle(self, *args, **options):
        user, _ = get_user_model().objects.get_or_create(username="demo", defaults={"email": "demo@example.com"})
        category, _ = Category.objects.get_or_create(name="বাংলা ও বিশ্ব ইতিহাস", defaults={"color": "#b45309"})
        tag, _ = Tag.objects.get_or_create(name="ভাষা / Language", defaults={"created_by": user})
        examples = (
            ("Bengali year 1370 / বাংলা ১৩৭০", "বাংলা ও English mixed historical entry.", BENGALI_BD, 1370, None, None, True),
            ("Bengali Language Movement", "ভাষা আন্দোলন, ২১ ফেব্রুয়ারি ১৯৫২।", GREGORIAN, 1952, 2, 21, True),
            ("Ides of March", "A BCE date demonstration.", GREGORIAN, -44, 3, 15, True),
            ("Private research note", "Only its owner can see this entry.", GREGORIAN, 1971, None, None, False),
        )
        for title, description, calendar, year, month, day, published in examples:
            event, _ = HistoricalEvent.objects.update_or_create(
                owner=user,
                title=title,
                defaults={
                    "description": description,
                    "category": category,
                    "start_calendar": calendar,
                    "start_year": year,
                    "start_month": month,
                    "start_day": day,
                    "is_published": published,
                },
            )
            event.tags.add(tag)
        self.stdout.write(self.style.SUCCESS("Demo data ready."))
