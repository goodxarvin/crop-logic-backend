import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from celery.schedules import crontab

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


def _get_csv_env(name, default=""):
    return [
        item.strip()
        for item in os.environ.get(name, default).split(",")
        if item.strip()
    ]


SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-only")
DEBUG = os.environ.get("DEBUG", "0") == "1"
ALLOWED_HOSTS = list(
    dict.fromkeys(
        _get_csv_env("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0")
        + ["web", "backend-web", os.environ.get("HOSTNAME", "")]
    )
)

AUTH_USER_MODEL = "account.User"

AUTHENTICATION_BACKENDS = [
    "account.backends.MultiFieldBackend",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "auth.apps.AuthConfig",
    "account.apps.AccountConfig",
    "farm_hub.apps.FarmHubConfig",
    "device_hub.apps.DeviceHubConfig",
    "subscriptions.apps.SubscriptionsConfig",
    "access_control.apps.AccessControlConfig",
    "dashboard",
    "crop_health.apps.CropHealthConfig",
    "soil.apps.SoilConfig",
    "crop_zoning",
    "pest_detection",
    "water.apps.WaterConfig",
    "irrigation",
    "yield_harvest.apps.YieldHarvestConfig",
    "economic_overview.apps.EconomicOverviewConfig",
    "farm_alerts.apps.FarmAlertsConfig",
    "fertilization",
    "farm_ai_assistant",
    "notifications.apps.NotificationsConfig",
    "plants.apps.PlantsConfig",
    "farmer_calendar.apps.FarmerCalendarConfig",
    "farmer_todos.apps.FarmerTodosConfig",
    "external_api_adapter.apps.ExternalApiAdapterConfig",
    "rest_framework",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "corsheaders",
    "address.apps.AddressConfig",
    "commerce_catalog.apps.CommerceCatalogConfig",
    "pricing.apps.PricingConfig",
    "wallet.apps.WalletConfig",
    "ledger.apps.LedgerConfig",
    "cart.apps.CartConfig",
    "checkout.apps.CheckoutConfig",
    "order.apps.OrderConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "access_control.middleware.RouteFeatureAccessMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

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

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.mysql"),
        "NAME": os.environ.get("DB_NAME", "croplogic"),
        "USER": os.environ.get("DB_USER", "croplogic"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv(
            "CACHE_URL", os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
        ),
        "KEY_PREFIX": "croplogic",
    }
}

PEST_DISEASE_RISK_SUMMARY_CACHE_TTL = int(
    os.getenv("PEST_DISEASE_RISK_SUMMARY_CACHE_TTL", "14400")
)
WATER_NEED_PREDICTION_CACHE_TTL = int(
    os.getenv("WATER_NEED_PREDICTION_CACHE_TTL", "14400")
)
SOIL_SUMMARY_CACHE_TTL = int(os.getenv("SOIL_SUMMARY_CACHE_TTL", "14400"))
SOIL_ANOMALIES_CACHE_TTL = int(os.getenv("SOIL_ANOMALIES_CACHE_TTL", "14400"))

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "access_control.permissions.FeatureAccessPermission",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "config.exception_handler.custom_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "CropLogic API",
    "DESCRIPTION": "Swagger/OpenAPI documentation for all CropLogic API endpoints.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "SCHEMA_PATH_PREFIX": r"/api/",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "SensorExternalApiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "Use API key 12345 for sensor external API endpoints.",
            }
        }
    },
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
}


SMS_IR_API_KEY = os.environ.get("SMS_IR_API_KEY", "")
SMS_IR_LINE_NUMBER = int(os.environ.get("SMS_IR_LINE_NUMBER", "300000000000"))

CORS_ALLOW_ALL_ORIGINS = DEBUG

USE_EXTERNAL_API_MOCK = os.getenv("USE_EXTERNAL_API_MOCK", "false").lower() == "true"
EXTERNAL_API_TIMEOUT = int(os.getenv("EXTERNAL_API_TIMEOUT", "30"))

ACCESS_CONTROL_AUTHZ_ENABLED = (
    os.getenv("ACCESS_CONTROL_AUTHZ_ENABLED", "true").lower() == "true"
)
ACCESS_CONTROL_AUTHZ_BASE_URL = os.getenv(
    "ACCESS_CONTROL_AUTHZ_BASE_URL",
    "http://croplogic-accsess-opa:8181",
)
ACCESS_CONTROL_AUTHZ_BATCH_PATH = os.getenv(
    "ACCESS_CONTROL_AUTHZ_BATCH_PATH", "/v1/data/croplogic/authz/batch_decision"
)
ACCESS_CONTROL_AUTHZ_TIMEOUT = int(
    os.getenv("ACCESS_CONTROL_AUTHZ_TIMEOUT", str(EXTERNAL_API_TIMEOUT))
)
ACCESS_CONTROL_AUTHZ_CACHE_TIMEOUT = int(
    os.getenv("ACCESS_CONTROL_AUTHZ_CACHE_TIMEOUT", "300")
)

EXTERNAL_SERVICES = {
    "ai": {
        "base_url": os.getenv("AI_SERVICE_BASE_URL", "http://ai-web:8000"),
        "api_key": os.getenv("AI_SERVICE_API_KEY", ""),
        "host_header": os.getenv("AI_SERVICE_HOST_HEADER", "localhost"),
    },
    "farm_hub": {
        "base_url": os.getenv("FARM_HUB_SERVICE_BASE_URL", ""),
        "api_key": os.getenv("FARM_HUB_SERVICE_API_KEY", ""),
        "host_header": os.getenv("FARM_HUB_SERVICE_HOST_HEADER", ""),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
}

CROP_ZONE_CHUNK_AREA_SQM = float(os.getenv("CROP_ZONE_CHUNK_AREA_SQM", "10000"))
CROP_ZONE_TASK_STALE_SECONDS = int(os.getenv("CROP_ZONE_TASK_STALE_SECONDS", "300"))

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
NOTIFICATION_REDIS_URL = os.getenv("NOTIFICATION_REDIS_URL", CELERY_BROKER_URL)
EXTERNAL_NOTIFICATION_API_KEY = os.getenv("EXTERNAL_NOTIFICATION_API_KEY", "12345")
SENSOR_EXTERNAL_API_KEY = os.getenv("SENSOR_EXTERNAL_API_KEY", "12345")
FARM_DATA_API_HOST = os.getenv("FARM_DATA_API_HOST", "")
FARM_DATA_API_PORT = os.getenv("FARM_DATA_API_PORT", "")
FARM_DATA_API_PATH = os.getenv("FARM_DATA_API_PATH", "/api/farm-data/")
FARM_DATA_API_KEY = os.getenv("FARM_DATA_API_KEY", "")
FARM_DATA_API_TIMEOUT = int(
    os.getenv("FARM_DATA_API_TIMEOUT", str(EXTERNAL_API_TIMEOUT))
)
CELERY_TASK_DEFAULT_QUEUE = os.getenv("CELERY_TASK_DEFAULT_QUEUE", "default")
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = int(
    os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "1")
)
CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "120"))
CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "90"))
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = (
    os.getenv("CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP", "true").lower() == "true"
)
FARM_ALERTS_AI_SYNC_CRON_MINUTE = os.getenv("FARM_ALERTS_AI_SYNC_CRON_MINUTE", "0")
FARM_ALERTS_AI_SYNC_CRON_HOUR = os.getenv("FARM_ALERTS_AI_SYNC_CRON_HOUR", "*")

CELERY_BEAT_SCHEDULE = {
    "sync-farm-alert-trackers": {
        "task": "farm_alerts.tasks.sync_farm_alert_trackers",
        "schedule": crontab(
            minute=FARM_ALERTS_AI_SYNC_CRON_MINUTE,
            hour=FARM_ALERTS_AI_SYNC_CRON_HOUR,
        ),
    },
    "expired_checkout_check": {
        "task": "checkout.tasks.expire_abandoned_checkout_sessions",
        "schedule": 1800.0,
    },
    "expired_order_check": {
        "task": "order.tasks.cancel_order_after_3_days",
        "schedule": 50.0,
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "farm_ai_assistant_file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "farm_ai_assistant.log",
            "formatter": "standard",
        },
        "farm_alerts_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "farm_alerts.log",
            "formatter": "standard",
        },
        "external_api_adapter_file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "external_api_adapter.log",
            "formatter": "standard",
        },
    },
    "loggers": {
        "farm_ai_assistant": {
            "handlers": ["farm_ai_assistant_file"],
            "level": "WARNING",
            "propagate": False,
        },
        "farm_alerts": {
            "handlers": ["farm_alerts_file"],
            "level": "INFO",
            "propagate": False,
        },
        "external_api_adapter": {
            "handlers": ["external_api_adapter_file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
