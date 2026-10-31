from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

User = get_user_model()


class LoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester", email="tester@example.com", password="Trender!2026",
        )

    def _login(self, username_or_email):
        return self.client.post(
            reverse("trender_auth:login"),
            {"username": username_or_email, "password": "Trender!2026"},
        )

    def test_login_with_username(self):
        res = self._login("tester")
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.json())

    def test_login_with_email(self):
        res = self._login("tester@example.com")
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.json())

    def test_login_with_email_case_insensitive(self):
        res = self._login("TESTER@EXAMPLE.COM")
        self.assertEqual(res.status_code, 200)

    def test_login_wrong_password_still_401(self):
        res = self.client.post(
            reverse("trender_auth:login"), {"username": "tester", "password": "wrong-password"},
        )
        self.assertEqual(res.status_code, 401)

    def test_login_unknown_identifier_401(self):
        res = self._login("nobody@example.com")
        self.assertEqual(res.status_code, 401)
