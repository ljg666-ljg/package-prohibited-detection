# 包裹违禁物品检测系统 - 生产环境配置

import os
from config.settings import *

# 安全 — 关闭 DEBUG
DEBUG = False

# 替换为你服务器的公网 IP
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'YOUR_SERVER_IP']

# 生产环境密钥 — 部署时替换为随机生成的 key
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-me-to-a-random-secret-key')

# 静态文件
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# 数据库 — 生产环境用 PostgreSQL，这里先用 SQLite
# 如果要切换 PostgreSQL，取消下面注释：
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get('DB_NAME', 'ppd_db'),
#         'USER': os.environ.get('DB_USER', 'ppd_user'),
#         'PASSWORD': os.environ.get('DB_PASSWORD', ''),
#         'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
#         'PORT': os.environ.get('DB_PORT', '5432'),
#     }
# }

# CSRF & Session
CSRF_COOKIE_SECURE = False  # 无 HTTPS 时设为 False
SESSION_COOKIE_SECURE = False

# Celery
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')

# Channels — 生产环境用 Redis
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [('127.0.0.1', 6379)]},
    },
}

# 日志
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[%(levelname)s] %(asctime)s %(module)s %(message)s'},
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'WARNING',
    },
}

print(f'[生产模式] DEBUG={DEBUG}, ALLOWED_HOSTS={ALLOWED_HOSTS}')
