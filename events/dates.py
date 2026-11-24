from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.utils.translation import get_language

GREGORIAN = "GREGORIAN"
BENGALI_BD = "BENGALI_BD"
CALENDAR_CHOICES = ((GREGORIAN, "Gregorian"), (BENGALI_BD, "Bangladesh Bengali"))

BENGALI_MONTHS_EN = (
    "Boishakh", "Joishtho", "Asharh", "Srabon", "Bhadro", "Ashwin",
    "Kartik", "Agrahayan", "Poush", "Magh", "Falgun", "Chaitra",
)
BENGALI_MONTHS_BN = (
    "বৈশাখ", "জ্যৈষ্ঠ", "আষাঢ়", "শ্রাবণ", "ভাদ্র", "আশ্বিন",
    "কার্তিক", "অগ্রহায়ণ", "পৌষ", "মাঘ", "ফাল্গুন", "চৈত্র",
)
GREGORIAN_MONTHS_EN = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
GREGORIAN_MONTHS_BN = (
    "জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন",
    "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর",
)

_BN_TO_ASCII = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_ASCII_TO_BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


@dataclass(frozen=True, order=True)
class DatePoint:
    year: int
    month: int
    day: int


@dataclass(frozen=True)
class DateBounds:
    lower: DatePoint
    upper: DatePoint


def normalize_digits(value):
    return str(value).translate(_BN_TO_ASCII).strip() if value not in (None, "") else value


def localize_digits(value, language=None):
    text = str(value)
    return text.translate(_ASCII_TO_BN) if (language or get_language() or "en").startswith("bn") else text


def astronomical_year(stored_year):
    return stored_year + 1 if stored_year < 0 else stored_year


def is_gregorian_leap(year):
    year = astronomical_year(year)
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def gregorian_month_length(year, month):
    if month == 2:
        return 29 if is_gregorian_leap(year) else 28
    if month in (4, 6, 9, 11):
        return 30
    return 31


def validate_components(calendar, year, month=None, day=None):
    if year is None:
        raise ValidationError("Year is required.")
    if calendar == BENGALI_BD and year < 1:
        raise ValidationError("Bengali year must be positive.")
    if calendar == GREGORIAN and year == 0:
        raise ValidationError("Gregorian calendar has no year zero.")
    if month is not None and not 1 <= month <= 12:
        raise ValidationError("Month must be between 1 and 12.")
    if day is not None and month is None:
        raise ValidationError("Choose a month before entering a day.")
    if day is not None:
        maximum = bengali_month_length(year, month) if calendar == BENGALI_BD else gregorian_month_length(year, month)
        if not 1 <= day <= maximum:
            raise ValidationError(f"Day must be between 1 and {maximum} for this month.")


def bengali_month_length(year, month):
    if month <= 6:
        return 31
    if month == 11:
        return 30 if is_gregorian_leap(year + 594) else 29
    return 30


def _next_gregorian(point):
    if point.day < gregorian_month_length(point.year, point.month):
        return DatePoint(point.year, point.month, point.day + 1)
    if point.month < 12:
        return DatePoint(point.year, point.month + 1, 1)
    return DatePoint(point.year + 1, 1, 1)


def _add_days(point, count):
    for _ in range(count):
        point = _next_gregorian(point)
    return point


def bengali_to_gregorian(year, month, day):
    validate_components(BENGALI_BD, year, month, day)
    offset = sum(bengali_month_length(year, item) for item in range(1, month)) + day - 1
    return _add_days(DatePoint(year + 593, 4, 14), offset)


def calendar_bounds(calendar, year, month=None, day=None):
    validate_components(calendar, year, month, day)
    if calendar == BENGALI_BD:
        lower_month, lower_day = month or 1, day or 1
        upper_month = month or 12
        upper_day = day or bengali_month_length(year, upper_month)
        return DateBounds(
            bengali_to_gregorian(year, lower_month, lower_day),
            bengali_to_gregorian(year, upper_month, upper_day),
        )
    lower_month, lower_day = month or 1, day or 1
    upper_month = month or 12
    upper_day = day or gregorian_month_length(year, upper_month)
    return DateBounds(DatePoint(year, lower_month, lower_day), DatePoint(year, upper_month, upper_day))


def format_source_date(calendar, year, month=None, day=None, language=None):
    language = language or get_language() or "en"
    bn = language.startswith("bn")
    number = lambda value: localize_digits(value, language)
    if calendar == BENGALI_BD:
        parts = []
        if day:
            parts.append(number(day))
        if month:
            parts.append((BENGALI_MONTHS_BN if bn else BENGALI_MONTHS_EN)[month - 1])
        parts.append(number(year))
        parts.append("বঙ্গাব্দ" if bn else "Bangabda")
        bounds = calendar_bounds(calendar, year, month, day)
        if not month:
            span = f"{number(bounds.lower.year)}–{number(bounds.upper.year)}"
        else:
            span = format_gregorian_point(bounds.lower, language)
            if bounds.upper != bounds.lower:
                span += f"–{format_gregorian_point(bounds.upper, language)}"
        return f"{' '.join(parts)} ({span})"
    era = "খ্রিস্টপূর্ব" if bn and year < 0 else "খ্রিস্টাব্দ" if bn else "BCE" if year < 0 else "CE"
    parts = []
    if day:
        parts.append(number(day))
    if month:
        parts.append((GREGORIAN_MONTHS_BN if bn else GREGORIAN_MONTHS_EN)[month - 1])
    parts.extend((number(abs(year)), era))
    return " ".join(parts)


def format_gregorian_point(point, language=None):
    language = language or get_language() or "en"
    bn = language.startswith("bn")
    months = GREGORIAN_MONTHS_BN if bn else GREGORIAN_MONTHS_EN
    return f"{localize_digits(point.day, language)} {months[point.month - 1]} {localize_digits(abs(point.year), language)}"
