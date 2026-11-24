# Historical Calendar UI Integration

This directory contains a Django-ready UI layer. It does not contain models, views, URL configuration, migrations, or authentication logic.

## Build assets

```bash
npm install
npm run build
npm test
```

Use `npm run watch:css` and `npm run watch:js` in separate terminals during development. Django must include the project `templates/` directory and serve `static/` through `django.contrib.staticfiles`.

Compiled files:

- `static/dist/app.v1.css`
- `static/dist/app.v1.js`
- `static/dist/timeline.v3.9.13.css`

## Required named URLs

| Name | Purpose |
| --- | --- |
| `core:landing` | Public landing page |
| `core:public_timeline` | Published timeline |
| `core:dashboard` | Authenticated dashboard |
| `accounts:login` | Sign in |
| `accounts:logout` | POST-only sign out |
| `accounts:register` | Registration |
| `accounts:profile` | Profile editing |
| `events:list` | Owner event list |
| `events:create` | Event creation |
| `events:detail` | Owner or published event detail |
| `events:edit` | Owner event editing |
| `events:delete` | Owner event deletion |

## Timeline page context

Both timeline pages require:

- `categories`: category objects with `name` and `slug`;
- `tags`: tag objects with `name` and `slug`;
- `selected_tags`: selected slug list;
- `filters`: object or dictionary with current filter values;
- `era_choices`: tuples for all, BCE, and CE choices;
- `public_feed_url` or `private_feed_url`: absolute or site-relative JSON endpoint.

Dashboard also uses `event_stats.total`, `event_stats.published`, `event_stats.private`, `event_form`, and `month_choices`.

The feed must return TimelineJS data:

```json
{
  "scale": "human",
  "events": [
    {
      "unique_id": "event-42",
      "start_date": {
        "year": -44,
        "month": 3,
        "day": 15,
        "display_date": "15 March 44 BCE"
      },
      "text": {
        "headline": "The Ides of March",
        "text": "<p>Escaped plain-text description</p>"
      },
      "group": "World History"
    }
  ]
}
```

Only include known month and day values. Add `end_date` only for range events. Public endpoints must exclude private events.

## Event form contract

The reusable partial expects a bound Django form and `month_choices`. The form fields are:

- `title`, `description`, `category`, `tags`, `new_tags`, `is_published`;
- `start_year_abs`, `start_era`, `start_month`, `start_day`;
- `end_year_abs`, `end_era`, `end_month`, `end_day`.

Server code must convert positive absolute years to signed integers. `BCE` negates the value; `CE` keeps it positive. Reject zero, require a month when a day exists, and validate optional end dates on the server.

## Other template context

- `events/event_list.html`: `events`, optional `page_obj`, and `pagination_query`.
- `events/event_detail.html`: `event` with `display_date`, category, tags, owner, and publication state.
- `events/event_form.html`: `form`, optional `event`, and `month_choices`.
- `events/event_confirm_delete.html`: `event`.
- Authentication and profile templates expect conventional bound Django forms.

## Accessibility and progressive enhancement

Create, edit, authentication, profile, and deletion flows use regular forms and remain functional without JavaScript. Timeline filtering and the desktop creation dialog are enhancements. Keep server validation authoritative and return bound forms with field errors after invalid submissions.
