"""Google 로그인: 프론트(Google Identity Services)가 받은 ID 토큰을 검증하고 사용자와 연결한다."""
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from google.auth.exceptions import TransportError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

User = get_user_model()

_USERNAME_MAX = User._meta.get_field("username").max_length


class GoogleAuthError(Exception):
    pass


def verify_id_token(token):
    """서명·만료·발급자·aud(=GOOGLE_CLIENT_ID)를 검증하고 이메일이 확인된 계정인지 본다."""
    try:
        claims = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
    except ValueError as exc:
        raise GoogleAuthError(f"유효하지 않은 Google 토큰입니다: {exc}") from exc
    except TransportError as exc:  # Google 공개키를 받아오지 못함
        raise GoogleAuthError("Google 인증 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.") from exc

    if not claims.get("email") or not claims.get("email_verified"):
        raise GoogleAuthError("이메일이 확인된 Google 계정만 사용할 수 있습니다.")
    return claims


def _unique_username(email):
    base = re.sub(r"[^\w.@+-]", "", email.split("@")[0])[:_USERNAME_MAX - 4] or "user"
    username, n = base, 1
    while User.objects.filter(username__iexact=username).exists():
        n += 1
        username = f"{base}{n}"
    return username


def get_or_create_user(claims):
    """같은 이메일의 계정이 있으면 그 계정으로 로그인하고, 없으면 비밀번호 없는 계정을 만든다.

    Google이 이메일 소유를 확인했으므로(email_verified) 기존 이메일 가입 계정과 연결해도 된다.
    """
    email = claims["email"]
    user = User.objects.filter(email__iexact=email).first()
    if user:
        return user, False

    try:
        with transaction.atomic():
            user = User(username=_unique_username(email), email=email,
                        first_name=claims.get("given_name", "")[:150],
                        last_name=claims.get("family_name", "")[:150])
            user.set_unusable_password()
            user.save()
    except IntegrityError:  # 같은 이메일로 동시에 요청이 들어온 경우
        return User.objects.get(email__iexact=email), False
    return user, True
