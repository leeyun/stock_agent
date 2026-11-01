from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
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


@override_settings(GOOGLE_CLIENT_ID="test-client.apps.googleusercontent.com")
class GoogleLoginTests(APITestCase):
    VERIFY = "apps.trender_auth.google.id_token.verify_oauth2_token"

    def _claims(self, **overrides):
        return {"email": "new@gmail.com", "email_verified": True,
                "given_name": "길동", "family_name": "홍", **overrides}

    def _post(self, claims=None, side_effect=None):
        with patch(self.VERIFY, return_value=claims, side_effect=side_effect) as verify:
            res = self.client.post(reverse("trender_auth:google"), {"id_token": "token"})
        return res, verify

    def test_config_returns_client_id(self):
        res = self.client.get(reverse("trender_auth:google"))
        self.assertEqual(res.json(), {"client_id": "test-client.apps.googleusercontent.com"})

    def test_new_user_is_created_with_unusable_password_and_default_group(self):
        res, verify = self._post(self._claims())

        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.json()["created"])
        self.assertIn("access", res.json())
        self.assertEqual(verify.call_args.args[0], "token")
        self.assertEqual(verify.call_args.args[2], "test-client.apps.googleusercontent.com")
        user = User.objects.get(email="new@gmail.com")
        self.assertEqual(user.username, "new")
        self.assertFalse(user.has_usable_password())
        self.assertTrue(user.watchlist_groups.filter(is_default=True).exists())

    def test_existing_email_logs_into_same_account(self):
        user = User.objects.create_user(username="tester", email="Tester@Gmail.com", password="Trender!2026")
        res, _ = self._post(self._claims(email="tester@gmail.com"))

        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()["created"])
        self.assertEqual(res.json()["user"]["id"], user.id)
        self.assertEqual(User.objects.count(), 1)

    def test_username_collision_gets_suffix(self):
        User.objects.create_user(username="new", email="other@example.com", password="Trender!2026")
        self._post(self._claims())
        self.assertEqual(User.objects.get(email="new@gmail.com").username, "new2")

    def test_invalid_token_is_401(self):
        res, _ = self._post(side_effect=ValueError("Token expired"))
        self.assertEqual(res.status_code, 401)
        self.assertEqual(User.objects.count(), 0)

    def test_unverified_email_is_401(self):
        res, _ = self._post(self._claims(email_verified=False))
        self.assertEqual(res.status_code, 401)
        self.assertEqual(User.objects.count(), 0)

    def test_inactive_user_is_403(self):
        User.objects.create_user(username="tester", email="new@gmail.com", password="x", is_active=False)
        res, _ = self._post(self._claims())
        self.assertEqual(res.status_code, 403)

    def test_missing_token_is_400(self):
        res = self.client.post(reverse("trender_auth:google"), {})
        self.assertEqual(res.status_code, 400)

    @override_settings(GOOGLE_CLIENT_ID="")
    def test_disabled_when_client_id_missing(self):
        res, verify = self._post(self._claims())
        self.assertEqual(res.status_code, 503)
        verify.assert_not_called()
