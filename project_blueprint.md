# History Timeline — AI Implementation Blueprint

## Purpose

Use this document as the source of truth when Claude, Codex, or another coding agent builds this project. Implement the application in the repository; do not respond with a tutorial or isolated code snippets.

The application helps history and literature students create events, keep private research notes, publish selected events, and explore BCE and CE material through an interactive timeline.

`ui_generation_instruciton.md` provides supporting design context. If it conflicts with this blueprint, this blueprint wins.

## Agent operating rules

1. Inspect the repository, existing instructions, dependencies, and working tree before changing files.
2. Preserve working user code and unrelated changes. Never replace established behavior without explaining why.
3. Implement only one phase from this document per invocation unless the user explicitly requests more.
4. Complete the phase fully, including migrations, tests, documentation, and asset changes that belong to it.
5. Run all checks relevant to the completed phase. Fix failures caused by the implementation.
6. End each phase with a checkpoint report containing completed work, changed subsystems, migrations, checks, limitations, and the next phase.
7. Ask only about product decisions that cannot be discovered from the repository or this document.
8. Use environment variables for secrets and environment-specific configuration. Never commit credentials.
9. Pin all installed Python and npm dependencies in reproducible dependency files.
10. Prefer clear, conventional Django code suitable for a beginner-to-intermediate Python developer. Avoid unnecessary abstractions.
11. Keep templates server-rendered. Use progressive enhancement so core forms and navigation work without JavaScript.
12. Do not add features outside the first-release scope.

## First-release scope

Build these user journeys:

- Public visitor views the landing page, published timeline, and published event details.
- User registers, logs in, logs out, and edits a profile.
- Authenticated user views a private dashboard and manages owned events.
- User creates point-in-time events or events with an optional end date.
- User selects a staff-managed category and existing tags or creates reusable tags.
- User explicitly publishes or unpublishes an owned event.
- User filters timelines by text, category, tags, era, and year range.
- Staff manages categories and tags through Django admin.

Do not add media uploads, comments, collaboration, social features, custom staff administration screens, localization, or staff publication approval.

## Fixed technology stack

- Python and Django using a currently supported stable release
- PostgreSQL in development and production
- Django templates and Django authentication
- Compiled Tailwind CSS
- Vanilla JavaScript; no React, Vue, Next.js, or SPA framework
- TimelineJS 3 using `@knight-lab/timelinejs`
- Gunicorn as the production WSGI server
- WhiteNoise for static files
- Environment variables for configuration
- Generic provider-neutral production deployment

Choose mutually compatible stable versions at the start of Phase 1, pin the exact resolved versions, and record them in the README. Do not silently upgrade dependencies in later phases.

## Project architecture

Use these Django boundaries:

- `config`: project URLs, WSGI/ASGI, and environment-specific settings.
- `core`: landing page, public timeline, private dashboard, health check, and shared presentation logic.
- `accounts`: registration, authentication templates, and user profile.
- `events`: historical date domain, categories, tags, events, permissions, CRUD, filters, and JSON feeds.
- `templates`: project-level templates organized by app, plus reusable components and form partials.
- `assets`: Tailwind source and vanilla JavaScript source.
- `static/dist`: generated production CSS and JavaScript. Do not hand-edit generated files.
- `tests` or app-level `tests/`: model, form, view, permission, API, and browser tests.

Split settings into shared base and development/production modules. Development may use convenient defaults, but PostgreSQL remains required; do not introduce SQLite-only behavior.

## Data model contract

### `accounts.Profile`

- `user`: one-to-one relation to Django's configured user model, cascade on deletion.
- `display_name`: optional string, maximum 120 characters.
- `institution`: optional string, maximum 200 characters.
- `bio`: optional text.
- `created_at` and `updated_at`: timestamps.

Create the profile explicitly during registration or with `get_or_create` when profile access requires it. Do not depend on model-save signals.

### `events.Category`

- `name`: unique string, maximum 100 characters.
- `slug`: unique slug, maximum 120 characters.
- `description`: optional text.
- `color`: validated six-digit hexadecimal color with a leading `#`; default to a warm amber compatible with the UI.
- `created_at` and `updated_at`: timestamps.

Categories are shared. Only staff may create, rename, recolor, or delete them. Events reference categories with `PROTECT`. Use the validated color as a CSS custom property or sanitized inline style; do not construct dynamic Tailwind class names.

### `events.Tag`

- `name`: normalized, case-insensitively unique string, maximum 50 characters.
- `slug`: unique slug, maximum 70 characters.
- `created_by`: nullable relation to the creating user; use `SET_NULL` when that user is deleted.
- `created_at`: timestamp.

Normalize surrounding and repeated whitespace before checking uniqueness. Authenticated users may create tags while editing events. Tags are globally reusable. Only staff may rename or delete existing tags.

### `events.HistoricalEvent`

- `owner`: required user relation with `CASCADE` and reverse name `historical_events`.
- `title`: required string, maximum 200 characters.
- `description`: required plain text.
- `category`: required protected relation to `Category`.
- `tags`: optional many-to-many relation to `Tag`.
- `start_year`: required signed integer.
- `start_month`: nullable small positive integer.
- `start_day`: nullable small positive integer.
- `end_year`, `end_month`, and `end_day`: nullable integer components.
- `is_published`: boolean, default `False`, indexed.
- `created_at` and `updated_at`: timestamps.

Use Django integer fields, not `DateField`, `DateTimeField`, Python `date`, or JavaScript `Date`, for historical date storage and transport. Add practical indexes for owner dashboards, published feeds, category filtering, and chronological queries. Default ordering must be deterministic: historical start components followed by primary key.

## Historical date rules

The signed-year convention is mandatory:

- `-44` means 44 BCE.
- `1` means 1 CE.
- `0` is invalid because the user-facing calendar has no year zero.

Month and day are optional to support uncertain dates:

- A day cannot exist without a month.
- Month must be from 1 through 12.
- Day must be valid for the specified month and year.
- End-year absence means the event is a point event. When end year is absent, end month and end day must also be absent.

Validate dates with proleptic Gregorian rules. For leap-year calculation, map a BCE stored year with `astronomical_year = stored_year + 1`; positive CE years remain unchanged.

Validate ranges with bounded dates:

- Missing start month/day uses the earliest possible value: January and day 1.
- Missing end month uses December.
- Missing end day uses the last valid day of its month.
- Reject an end bound earlier than its start bound.

Keep date parsing, validation, comparison, and display formatting in reusable `events` domain helpers. Cover these helpers with focused unit tests.

## Form contract

Never show signed database years in editable controls. Each start or end date group uses a positive absolute year input, BCE/CE segmented control, optional month, and optional day.

Use stable form field names:

- `start_year_abs`, `start_era`, `start_month`, `start_day`;
- `end_year_abs`, `end_era`, `end_month`, `end_day`.

Era fields accept only `BCE` or `CE`. Convert cleaned absolute years and eras into signed model values on the server. JavaScript may improve the interaction but must not be the only validation or conversion layer.

The event form also contains title, description, category, existing tags, comma-separated new tag names, and an explicit publication control. Reuse one form and template partial for create, edit, modal, and dedicated-page rendering.

## Permissions and visibility

- Events are private by default.
- Owners may list, view, create, edit, publish, unpublish, and delete their own events.
- Authenticated non-owners cannot view or mutate another user's private event.
- Anyone may view a published event and public timeline data.
- Publishing needs no staff approval.
- Staff status does not silently grant event ownership; use Django admin for deliberate staff management.
- Apply identical visibility rules to HTML views and JSON feeds.
- Return `404` rather than revealing inaccessible private events where appropriate.
- Protect state-changing requests with POST and CSRF validation. Delete operations require confirmation.

Centralize reusable ownership/publication query logic in model querysets or small permission helpers. Do not duplicate inconsistent checks across views.

## Routes and view contract

Use named URLs and conventional Django views for:

- `/` — public landing page.
- `/timeline/` — public published timeline.
- `/dashboard/` — authenticated private dashboard.
- `/health/` — minimal application and database health check with no sensitive output.
- `/accounts/register/` — registration.
- `/accounts/login/` and `/accounts/logout/` — authentication.
- `/accounts/profile/` — authenticated profile view and edit.
- `/events/` — authenticated owner's paginated event list.
- `/events/new/` — event creation page and modal POST target.
- `/events/<int:pk>/` — event detail, available to owner or public when published.
- `/events/<int:pk>/edit/` — owner-only edit.
- `/events/<int:pk>/delete/` — owner-only confirmation and deletion.
- `/api/events/private/` — authenticated owner's TimelineJS feed.
- `/api/events/public/` — public published TimelineJS feed.

Successful create and edit requests use Post/Redirect/Get. Preserve filters and pagination where useful without accepting arbitrary redirect URLs.

## Filtering contract

Both timeline feeds support:

- `q`: case-insensitive search across title and description.
- `category`: one category slug.
- `tag`: repeated tag slug; multiple values use OR semantics.
- `era`: `BCE` or `CE`, based on start year.
- `year_from`: optional signed inclusive lower start-year bound.
- `year_to`: optional signed inclusive upper start-year bound.

Return a structured `400` JSON response for malformed era or year values. Eliminate duplicates caused by many-to-many joins. Use the same filter service for public and private feeds after selecting the correct visibility queryset.

Visible year-range controls use positive values and era selectors. Vanilla JavaScript converts them into signed query values before requesting timeline data.

## TimelineJS JSON contract

Return a TimelineJS 3 object, not internal model serialization:

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
        "headline": "Example event",
        "text": "<p>Escaped plain-text description</p>"
      },
      "group": "World History"
    }
  ]
}
```

Rules:

- Include only date components known by the user.
- Add `end_date` only when an end year exists.
- Pass BCE years as negative integers.
- Always provide human-readable `display_date`; never display `-44` to the user.
- Build stable `unique_id` values from event primary keys.
- Use category names as TimelineJS groups.
- Escape plain-text user content before wrapping it in any server-controlled markup needed by TimelineJS.
- Never expose owner email, profile data, unpublished events, or internal permission fields.

When filters change, fetch new JSON, replace the timeline container, and create a fresh TimelineJS instance. Preserve an active event when its stable ID remains in the result. Show distinct loading, empty, malformed-response, network-failure, and retry states.

## UI system

Create a clean academic interface with subtle historical character:

- `Libre Baskerville` for headings.
- `Inter` for controls and body text.
- Warm `amber-50` and `stone-50` surfaces.
- `stone-800` primary text and accessible muted slate/stone text.
- `amber-700` primary accents with accessible hover and focus states.

Use compiled Tailwind utilities and a small documented component layer. Do not use Tailwind's browser CDN in production. Configure template and JavaScript scanning so production builds retain every used class.

Required screens and states:

- public landing page, published timeline, and event detail;
- login and registration;
- private dashboard;
- paginated event list;
- owner/public event detail states;
- create and edit event form;
- create-event modal with dedicated-page fallback;
- delete confirmation and profile;
- loading, empty, validation, permission, not-found, and server-error states.

Dashboard layout:

- Desktop uses top navigation, persistent filter sidebar, and timeline as main content.
- Mobile uses compact navigation, a filter drawer, and a full-width timeline.
- Timeline receives approximately 65–75% of viewport height while leaving filters and status visible.
- New Event opens an accessible modal on desktop. `/events/new/` remains the mobile and no-JavaScript fallback.

Accessibility requirements:

- Use semantic landmarks, headings, labels, fieldsets, and buttons.
- Provide visible keyboard focus and sufficient color contrast.
- Associate validation messages with fields and announce form summaries.
- Implement modal focus entry, focus trap, Escape close, background inertness, and focus restoration.
- Make filter drawer and navigation keyboard-operable.
- Respect `prefers-reduced-motion`.
- Do not rely on color alone to communicate state.

## Frontend asset contract

- Keep source CSS in `assets/css/` and source JavaScript in `assets/js/`.
- Bundle TimelineJS and application JavaScript from pinned npm dependencies.
- Compile and minify assets into `static/dist/` for production.
- Provide npm scripts for watch mode, development build, production build, JavaScript tests, and browser tests.
- Keep date conversion, query construction, modal behavior, filter drawer behavior, and timeline initialization in small testable modules.

## Implementation phases

### Phase 1 — Foundation

- Create the Django project and `core`, `accounts`, and `events` apps.
- Add split settings, PostgreSQL configuration, environment loading, URLs, templates, static paths, and health check.
- Add pinned Python and npm dependency files.
- Configure Tailwind and JavaScript entry points without feature screens.
- Add `.env.example`, `.gitignore`, baseline tests, and initial README commands.

Checkpoint: project starts against PostgreSQL, health check and baseline tests pass, and frontend development/production builds complete.

### Phase 2 — Models and historical date domain

- Implement models and historical-date helpers exactly as specified.
- Create and inspect migrations.
- Register useful admin interfaces with search, filters, and safe list displays.
- Add model, constraint, helper, and admin permission tests.

Checkpoint: migrations apply to an empty PostgreSQL database and all model/date tests pass.

### Phase 3 — Authentication and permissions

- Implement registration, login, logout, profile editing, and authentication templates.
- Implement event visibility querysets and ownership helpers.
- Add anonymous, owner, non-owner, staff, and published-event permission tests.

Checkpoint: authentication works and the permission matrix passes without leaking private event existence.

### Phase 4 — Event CRUD and filtering

- Implement signed-year form conversion and server validation.
- Implement event list, detail, create, edit, publication, and delete flows.
- Implement category selection, existing-tag selection, and normalized new-tag creation.
- Add pagination and reusable filtering.
- Test forms, views, redirects, CSRF, tag normalization, and query behavior.

Checkpoint: event management works without JavaScript and ownership/date/filter tests pass.

### Phase 5 — UI system

- Build shared layout, typography, palette, components, navigation, messages, forms, and responsive structures.
- Build every required public, authentication, dashboard, event, profile, and error screen.
- Add accessible create-event modal while preserving dedicated-page fallback.
- Add filter sidebar/drawer and loading, empty, error, and validation states.

Checkpoint: compiled Tailwind retains required classes; screens pass responsive and keyboard review at mobile, tablet, and desktop sizes.

### Phase 6 — TimelineJS integration

- Implement private and public JSON feeds using shared filters and visibility rules.
- Serialize partial BCE/CE dates to the required schema.
- Integrate TimelineJS 3 with filters, instance recreation, active-event preservation, and status states.
- Add API contract, privacy, escaping, JavaScript unit, and browser interaction tests.

Checkpoint: BCE, CE, partial, point, and range events render; filters update without full-page reload; private data never appears publicly.

### Phase 7 — Quality and deployment

- Finish Django integration, JavaScript unit, browser-flow, and accessibility tests.
- Add deterministic `seed_demo` command with BCE, CE, partial-date, range, private, and published examples.
- Configure production security, Gunicorn, WhiteNoise, logging, static collection, and database-backed health checks.
- Document provider-neutral deployment, migrations, backups, restore tests, asset builds, rollback, and operations.
- Complete README setup and troubleshooting instructions.

Checkpoint: clean setup succeeds from documentation; full tests, production build, static collection, deployment checks, and accessibility checks pass.

## Required tests

At minimum, cover:

- 44 BCE converts to `-44`, persists, serializes as `-44`, and displays as `44 BCE`.
- 1 BCE and 1 CE are valid; year zero is rejected everywhere.
- Year-only, year-month, and full dates serialize without invented precision.
- Invalid month/day combinations and BCE leap-day cases fail correctly.
- Point events omit `end_date`.
- Optional, same-year, and BCE-to-CE ranges compare and render correctly.
- End-before-start ranges fail validation.
- Tag names normalize and remain case-insensitively unique.
- Anonymous, owner, non-owner, and staff requests follow the permission contract.
- Private events never appear in public HTML, searches, counts, or JSON.
- Published events appear on public timeline and detail pages.
- Search, category, repeated-tag OR, era, and signed year filters return distinct correct results.
- Malformed filters return structured `400` responses.
- User content cannot inject executable markup through TimelineJS.
- Modal and drawer support keyboard navigation and focus restoration.
- Layout works at representative mobile, tablet, and desktop viewports.
- Production Tailwind scan retains classes used in templates and JavaScript.

## Definition of done

The first release is complete only when:

- all seven checkpoints pass;
- migrations work on a clean PostgreSQL database;
- Python, JavaScript, browser, and accessibility tests pass;
- production CSS and JavaScript builds succeed;
- `collectstatic` succeeds;
- CRUD operations enforce ownership;
- public responses contain only published data;
- TimelineJS renders BCE, CE, partial, and range dates correctly;
- responsive layouts work across mobile, tablet, and desktop;
- no secrets or machine-specific paths are committed;
- README contains exact environment, database, install, migrate, seed, run, build, test, collect-static, and production commands.

## Deployment requirements

Keep deployment provider-neutral. Document these environment variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_SETTINGS_MODULE`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`

Production must disable debug mode, validate allowed hosts, trust only configured origins, use secure cookies under HTTPS, enable appropriate proxy/SSL settings, serve static assets through WhiteNoise or an external static host, and run with Gunicorn. Document migration ordering, backup before migration, rollback, logs, health checks, and restore verification without assuming a cloud provider.

## Final constraints

- English and Bangla interfaces are required. Event content may mix both languages.
- Public publishing is controlled by each owner and needs no staff approval.
- Categories are shared and staff-managed.
- Tags are shared; authenticated users may create them, but only staff may rename or delete them.
- PostgreSQL is mandatory.
- Historical date components remain integers through storage and API serialization.
- TimelineJS 3 is the only timeline library for the first release.
- Tailwind CSS is compiled; Bootstrap and Tailwind CDN builds are not permitted.
- The application remains server-rendered and progressively enhanced.
