from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import (
    OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view, inline_serializer,
)
from rest_framework import generics, serializers, status

from . import google
from .serializers import GoogleLoginSerializer, LoginSerializer, SignupSerializer, UserSerializer

User = get_user_model()

# TODO: ~~~API, 어떤 변수가 필요하다
# TODO: ~~~API
# TODO: ~~~API
# TODO: ~~~API
# TODO: ~~~API
# TODO: ~~~API
@extend_schema(
    tags=["auth"],
    summary="회원가입",
    description="계정을 생성하고 JWT 토큰을 즉시 발급한다. 별도 로그인 호출이 필요 없다.",
    responses={
        201: inline_serializer(
            name="SignupResponse",
            fields={
                "user": UserSerializer(),
                "access": serializers.CharField(),
                "refresh": serializers.CharField(),
            },
        ),
        400: OpenApiResponse(description="입력값 검증 실패"),
    },
    examples=[
        OpenApiExample(
            "요청 예시",
            request_only=True,
            value={
                "username": "tester",
                "email": "tester@example.com",
                "password": "Trender!2026",
                "password2": "Trender!2026",
            },
        ),
    ],
)
class SignupView(generics.CreateAPIView):
    queryset           = User.objects.all()
    serializer_class   = SignupSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user    = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user":    UserSerializer(user).data,
                "access":  str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["auth"],
    summary="로그인",
    description="username 과 password 로 access / refresh 토큰을 발급한다.",
    responses={
        200: inline_serializer(
            name="LoginResponse",
            fields={
                "user": UserSerializer(),
                "access": serializers.CharField(),
                "refresh": serializers.CharField(),
            },
        ),
        401: OpenApiResponse(description="자격 증명 실패"),
    },
)
class LoginView(TokenObtainPairView):
    serializer_class   = LoginSerializer
    permission_classes = [AllowAny]


@extend_schema_view(
    get=extend_schema(
        tags=["auth"],
        summary="Google 로그인 설정 조회",
        description="프론트가 Google 로그인 버튼을 띄울 때 쓸 OAuth 클라이언트 ID. 비어 있으면 Google 로그인 비활성.",
        responses={200: inline_serializer(name="GoogleConfigResponse",
                                          fields={"client_id": serializers.CharField()})},
    ),
    post=extend_schema(
        tags=["auth"],
        summary="Google 로그인",
        description=(
            "Google ID 토큰을 검증하고 JWT를 발급한다. 같은 이메일 계정이 있으면 그 계정으로 로그인하고, "
            "없으면 계정을 새로 만든다(201, 비밀번호 없이 Google로만 로그인)."
        ),
        request=GoogleLoginSerializer,
        responses={
            200: inline_serializer(
                name="GoogleLoginResponse",
                fields={
                    "user": UserSerializer(),
                    "access": serializers.CharField(),
                    "refresh": serializers.CharField(),
                    "created": serializers.BooleanField(),
                },
            ),
            201: OpenApiResponse(description="새 계정 생성 후 로그인 (응답 형식은 200과 같음)"),
            400: OpenApiResponse(description="토큰 누락"),
            401: OpenApiResponse(description="토큰 검증 실패 또는 이메일 미확인 계정"),
            403: OpenApiResponse(description="비활성화된 계정"),
            503: OpenApiResponse(description="서버에 GOOGLE_CLIENT_ID 미설정"),
        },
    ),
)
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({"client_id": settings.GOOGLE_CLIENT_ID})

    def post(self, request):
        if not settings.GOOGLE_CLIENT_ID:
            return Response({"detail": "Google 로그인이 설정되지 않았습니다."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            claims = google.verify_id_token(serializer.validated_data["id_token"])
        except google.GoogleAuthError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        user, created = google.get_or_create_user(claims)
        if not user.is_active:
            return Response({"detail": "비활성화된 계정입니다."}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user":    UserSerializer(user).data,
                "access":  str(refresh.access_token),
                "refresh": str(refresh),
                "created": created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


@extend_schema(
    tags=["auth"],
    summary="로그아웃",
    description=(
        "refresh 토큰을 블랙리스트에 등록한다. "
        "이미 발급된 access 토큰은 만료 시각까지 유효하므로 "
        "클라이언트에서 직접 폐기해야 한다."
    ),
    request=inline_serializer(
        name="LogoutRequest",
        fields={"refresh": serializers.CharField()},
    ),
    responses={
        205: OpenApiResponse(description="로그아웃 완료"),
        400: OpenApiResponse(description="토큰이 없거나 유효하지 않음"),
    },
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            RefreshToken(request.data["refresh"]).blacklist()
        except KeyError:
            return Response({"detail": "refresh 토큰이 필요합니다."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"detail": "유효하지 않은 토큰입니다."},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


@extend_schema_view(
    get=extend_schema(
        tags=["auth"],
        summary="내 정보 조회",
        responses={200: UserSerializer},
    ),
    put=extend_schema(
        tags=["auth"],
        summary="내 정보 전체 수정",
        responses={200: UserSerializer},
    ),
    patch=extend_schema(
        tags=["auth"],
        summary="내 정보 부분 수정",
        responses={200: UserSerializer},
    ),
)
class MeView(generics.RetrieveUpdateAPIView):
    serializer_class   = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user