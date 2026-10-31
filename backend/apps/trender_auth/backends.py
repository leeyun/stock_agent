from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """username 또는 email 중 아무거나 넣어도 로그인되도록 하는 인증 백엔드.

    simplejwt의 TokenObtainPairSerializer는 항상 USERNAME_FIELD("username") 키로
    authenticate()를 호출하므로, 그 값을 username 또는 email로 함께 조회한다.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None

        try:
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
