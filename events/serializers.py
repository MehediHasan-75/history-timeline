from django.utils.html import escape

from .dates import BENGALI_BD, format_source_date


def point_dict(year, month=None, day=None, display_date=None):
    value = {"year": year}
    if month is not None:
        value["month"] = month
    if day is not None:
        value["day"] = day
    if display_date:
        value["display_date"] = display_date
    return value


def serialize_event(event):
    display_start = format_source_date(event.start_calendar, event.start_year, event.start_month, event.start_day)
    if event.start_calendar == BENGALI_BD:
        start = point_dict(event.start_lower_year, event.start_lower_month, event.start_lower_day, display_start)
    else:
        start = point_dict(event.start_year, event.start_month, event.start_day, display_start)
    payload = {
        "unique_id": f"event-{event.pk}",
        "start_date": start,
        "text": {
            "headline": escape(event.title),
            "text": f"<p>{escape(event.description).replace(chr(10), '<br>')}</p>",
        },
        "group": event.category.name,
    }
    if event.end_year is not None:
        display_end = format_source_date(event.end_calendar, event.end_year, event.end_month, event.end_day)
        if event.end_calendar == BENGALI_BD:
            payload["end_date"] = point_dict(event.end_upper_year, event.end_upper_month, event.end_upper_day, display_end)
        else:
            payload["end_date"] = point_dict(event.end_year, event.end_month, event.end_day, display_end)
    elif event.start_calendar == BENGALI_BD and (event.start_month is None or event.start_day is None):
        payload["end_date"] = point_dict(event.start_upper_year, event.start_upper_month, event.start_upper_day, display_start)
    return payload
