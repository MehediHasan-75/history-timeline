from django.db.models import Q

from .dates import BENGALI_BD, GREGORIAN, calendar_bounds, normalize_digits


class FilterError(ValueError):
    pass


def parse_year(value, name):
    if value in (None, ""):
        return None
    try:
        year = int(normalize_digits(value))
    except (TypeError, ValueError):
        raise FilterError(f"{name} must be an integer.")
    if year == 0:
        raise FilterError(f"{name} cannot be zero.")
    return year


def filter_events(queryset, params):
    query = params.get("q", "").strip()
    if query:
        queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if params.get("category"):
        queryset = queryset.filter(category__slug=params["category"])
    tags = params.getlist("tag") if hasattr(params, "getlist") else params.get("tag", [])
    if tags:
        queryset = queryset.filter(tags__slug__in=tags)
    calendar = params.get("calendar", GREGORIAN) or GREGORIAN
    if calendar not in (GREGORIAN, BENGALI_BD):
        raise FilterError("calendar must be GREGORIAN or BENGALI_BD.")
    era = params.get("era", "")
    if era and era not in ("BCE", "CE"):
        raise FilterError("era must be BCE or CE.")
    if calendar == BENGALI_BD and era:
        raise FilterError("era cannot be combined with Bengali calendar filtering.")
    if era == "BCE":
        queryset = queryset.filter(start_lower_year__lt=0)
    elif era == "CE":
        queryset = queryset.filter(start_upper_year__gt=0)
    lower = parse_year(params.get("year_from"), "year_from")
    upper = parse_year(params.get("year_to"), "year_to")
    if lower is not None and upper is not None and lower > upper:
        raise FilterError("year_from cannot be greater than year_to.")
    if calendar == BENGALI_BD:
        if lower is not None:
            if lower < 1:
                raise FilterError("Bengali year_from must be positive.")
            lower = calendar_bounds(BENGALI_BD, lower).lower.year
        if upper is not None:
            if upper < 1:
                raise FilterError("Bengali year_to must be positive.")
            upper = calendar_bounds(BENGALI_BD, upper).upper.year
    if lower is not None:
        queryset = queryset.filter(start_upper_year__gte=lower)
    if upper is not None:
        queryset = queryset.filter(start_lower_year__lte=upper)
    return queryset.distinct()
