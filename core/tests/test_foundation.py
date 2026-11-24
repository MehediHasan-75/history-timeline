from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse


class FoundationPageTests(TestCase):
    def test_landing_page_renders(self):
        response = self.client.get(reverse("core:landing"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "History Timeline")

    def test_dashboard_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse("core:dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('core:dashboard')}",
            fetch_redirect_response=False,
        )

    def test_public_timeline_renders_with_empty_feed_shell(self):
        response = self.client.get(reverse("core:public_timeline"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/api/events/public/")

    def test_bangla_language_switch_changes_application_navigation(self):
        response = self.client.post(reverse("set_language"), {"language": "bn", "next": reverse("core:public_timeline")}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "সময়রেখা দেখুন")
        self.assertEqual(self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, "bn")


class HealthCheckTests(SimpleTestCase):
    @patch("core.views.database_is_ready", return_value=True)
    def test_health_reports_database_ready(self, database_is_ready):
        response = self.client.get(reverse("core:health"))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok", "database": "ok"})
        database_is_ready.assert_called_once_with()

    @patch("core.views.database_is_ready", return_value=False)
    def test_health_failure_hides_internal_error(self, database_is_ready):
        response = self.client.get(reverse("core:health"))

        self.assertEqual(response.status_code, 503)
        self.assertJSONEqual(
            response.content,
            {"status": "unavailable", "database": "unavailable"},
        )
        self.assertNotContains(response, "secret database detail", status_code=503)
        database_is_ready.assert_called_once_with()


class SettingsContractTests(SimpleTestCase):
    def test_postgresql_is_mandatory(self):
        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"],
            "django.db.backends.postgresql",
        )

    def test_project_template_and_static_directories_are_registered(self):
        self.assertIn(settings.BASE_DIR / "templates", settings.TEMPLATES[0]["DIRS"])
        self.assertIn(settings.BASE_DIR / "static", settings.STATICFILES_DIRS)

    @override_settings(DEBUG=False)
    def test_custom_404_page_renders(self):
        response = self.client.get("/missing-page/")

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "This page left no record", status_code=404)
