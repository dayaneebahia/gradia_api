import firebase_admin
from firebase_admin import credentials
from datetime import timedelta
from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Path to your service account key (use for local development)
FIREBASE_ADMIN_CREDENTIAL = "gradiafinance/config/gradia-dev-firebase-adminsdk.json"
if not os.path.isfile(FIREBASE_ADMIN_CREDENTIAL):
   raise ValueError(f"Firebase Admin Credential file not found at: {FIREBASE_ADMIN_CREDENTIAL}. Check your environment variable settings.")
cred = credentials.Certificate(FIREBASE_ADMIN_CREDENTIAL)
firebase_admin.initialize_app(cred)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-c_)ow&7+tk#+9^=&=&4t=kud+blb1&rs^=1hvo_vqc=n*=lrp='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'rest_framework',
    'finance',
    'corsheaders',
     "storages",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]


ROOT_URLCONF = 'gradiafinance.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]



WSGI_APPLICATION = 'gradiafinance.wsgi.application'

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://10.0.2.2:8000",   # For Android Emulator
    "http://192.168.1.100:8000",  # If accessing from another machine
    "http://localhost:19000",  # Expo Dev URL
    "http://localhost:19006",  # Expo Web Preview
]

CORS_ALLOW_ALL_ORIGINS = True  # TEMPORARY: Allow everything during testing
CORS_ALLOW_CREDENTIALS = True

AWS_ACCESS_KEY_ID = "AKIA4MTWMYOSNBSBFZES"
AWS_SECRET_ACCESS_KEY = "VAcgOaezAHVW+TX2pllvlQpT8s86NrSON5ccm8lQ"
AWS_STORAGE_BUCKET_NAME = "gradia"
AWS_S3_REGION_NAME = "us-east-1"  # Change to your AWS region
AWS_S3_CUSTOM_DOMAIN = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gradiafinance',
        'USER': 'postgres',
        'PASSWORD': 'admin',
        'HOST': 'postgres_db',  # Make sure this matches the service name in docker-compose.yml
        'PORT': '5432',
    }
}



# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'finance.authentication.FirebaseAuthentication',  # Add Firebase Authentication
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'finance.authentication.FirebaseAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}


