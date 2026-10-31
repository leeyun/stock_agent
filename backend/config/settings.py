import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
from celery.schedules import crontab

# ==============================================================================
# 0. 필수 설정 및 기본 경로 (BASICS)
# 1. 애플리케이션 정의 (APPLICATION DEFINITION)
# 2. 미들웨어 (MIDDLEWARE)
# 3. URL 및 템플릿 (URLS & TEMPLATES)
# 4. 국제화 (INTERNATIONALIZATION)
# 5. 보안 및 인증 (SECURITY & AUTHENTICATION)
# 6. 데이터베이스 (DATABASE)
# 7. 파일 관리 (FILES: Static, Media)
# 8. 서드파티 라이브러리 설정 (THIRD-PARTY SETTINGS: REST/CORS/JWT/Spectacular)
# 9. 로깅 (LOGGING)
# ==============================================================================

# ==============================================================================
# 0. 필수 설정 및 기본 경로 (BASICS)
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# TODO: 장고 시크릿키를 연결해야합니다. [완료]
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# WARN: 개발 중에만 사용하고 배포 시에는 실제 도메인만 명시하세요.
ALLOWED_HOSTS = ["*"]

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================================================================
# 1. 애플리케이션 정의 (APPLICATION DEFINITION)
# ==============================================================================
INSTALLED_APPS = [
    # 1. Django 기본 앱
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 2. 서드파티 앱
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework_docs',
    'drf_spectacular',
    'corsheaders',

    # 3. 로컬 앱
    "apps.trender_auth",
    "apps.trender_stock",
    "apps.trender_watchlist",
    "apps.trender_news",
    "apps.trender_digest",
]


# ==============================================================================
# 2. 미들웨어 (MIDDLEWARE)
# ==============================================================================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ==============================================================================
# 3. URL 및 템플릿 (URLS & TEMPLATES)
# ==============================================================================
ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
# FIXED: channels를 없애서 ASGI 삭제함
# ASGI_APPLICATION = 'config.asgi.application'


# ==============================================================================
# 4. 국제화 (INTERNATIONALIZATION)
# ==============================================================================
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True   # INFO: 미국장/한국장을 함께 다루므로 DB 에는 UTC 로 저장하고 표시할 때만 변환


# ==============================================================================
# 5. 보안 및 인증 (SECURITY & AUTHENTICATION)
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# 커스텀 유저 모델 지정
AUTH_USER_MODEL = "trender_auth.User"

# 로그인 시 username, email 둘 다 허용
AUTHENTICATION_BACKENDS = [
    "apps.trender_auth.backends.EmailOrUsernameModelBackend",
    "django.contrib.auth.backends.ModelBackend",
]

## CSRF 신뢰 출처. ngrok 은 스킴(https://)까지 포함해야 하며 ALLOWED_HOSTS 와 문법이 다름
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://*.ngrok-free.app",
]

# Ngrok 같은 프록시 서버가 씌워준 HTTPS를 장고가 믿도록 설정
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 호스트 Ngrok 도메인으로 인식하게 설정
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True


# ==============================================================================
# 6. 데이터베이스 (DATABASE)
# ==============================================================================

# TODO: pgvector로 임베딩을 쓰려면 Postgres로 옮겨야 합니다.
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.environ["POSTGRES_DB"],
#         "USER": os.environ["POSTGRES_USER"],
#         "PASSWORD": os.environ["POSTGRES_PASSWORD"],
#         "HOST": os.getenv("POSTGRES_HOST", "localhost"),
#         "PORT": os.getenv("POSTGRES_PORT", "5432"),
#     }
# }
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 10,
        }
    }
}


# ==============================================================================
# 7. 파일 관리 (FILES: Static, Media)
# ==============================================================================
STATIC_URL = "static/"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 고해상도 사진 업로드 및 처리용 메모리 세팅
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB


# ==============================================================================
# 8. 서드파티 라이브러리 설정 (THIRD-PARTY SETTINGS: REST/CORS/JWT/Spectacular)
# ==============================================================================
# REST Framework 설정
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# CORS 세부 설정
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# JWT 설정
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    
    "USER_ID_FIELD": "id", # User pk는 BigAutoField(정수)라 id로 매핑
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'USER_ID_CLAIM': 'user_id',
}

# Swagger (Spectacular) 설정
SPECTACULAR_SETTINGS = {
    "TITLE": "Trender API",
    "DESCRIPTION": "종목별 뉴스 집계·요약·호재/악재 판단 API",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,   # 새로고침해도 토큰 유지
        "displayRequestDuration": True,
    },
}

# Celery 설정 (백그라운드 AI 처리용)
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0' 
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_IGNORE_RESULT = False
CELERY_RESULT_EXPIRES = 3600
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'Asia/Seoul'

# Celery beat 스케줄 (celery -A config beat 로 별도 실행)
CELERY_BEAT_SCHEDULE = {
    "sync-krx-stocks-daily": {
        "task": "apps.trender_stock.tasks.sync_krx_stocks_task",
        "schedule": crontab(hour=8, minute=30),  # 장 시작(09:00) 전 종목 마스터 동기화
    },
    "sync-krx-quotes-market-hours": {
        "task": "apps.trender_stock.tasks.sync_krx_quotes_task",
        "schedule": crontab(minute="*/5", hour="9-15", day_of_week="mon-fri"),  # 평일 장중 5분마다
    },
    "collect-news-hourly": {
        "task": "apps.trender_news.tasks.collect_news_task",
        # 기사 1건당 Gemini 호출 1번 + 4.2초 대기가 들어가서 시세보다 훨씬 낮은 빈도로 실행
        "schedule": crontab(minute=0, hour="9-16", day_of_week="mon-fri"),  # 평일 장중 매시 정각
    },
}

# Ollama AI API 설정 (환경변수 미설정 시 기본값 fallback)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# FIXED: InMemoryChannelLayer 는 CONFIG.hosts 를 사용하지 않아 Redis 설정이 무의미하고,
#        프로세스 하나 안에서만 동작해서 Celery 워커 → WebSocket 푸시가 불가능합니다.
#        실시간 푸시를 붙일 때 channels_redis 로 교체하세요.
#
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
#     },
# }

# ==============================================================================
# 9. 로깅 (LOGGING)
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    "formatters": {
        # ADDED: 포맷터가 없어서 시각과 레벨이 안 찍혔다..
        "verbose": {
            "format": "[{asctime}] {levelname} {name} — {message}",
            "style": "{",
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django.log',
            "formatter": "verbose",
            "encoding": "utf-8",   # ADDED: 없어서 한국어 로그가 깨짐현상 발생
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        # FIXED: 로거 이름 'config' → 'apps'.
        #        실제 코드는 apps.trender_news 등에 있어서 'config' 로거로는
        #        아무것도 수집되지 않았음
        "apps": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}