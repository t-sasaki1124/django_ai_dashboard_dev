from pathlib import Path
from dotenv import load_dotenv
import os

# .envファイルを読み込む
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'dev-secret-key'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',  # ← 追加
    'portal',  # ユーザーポータルアプリ
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',  # キャッシュミドルウェア（上）
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',  # キャッシュミドルウェア（下）
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'myapp' / 'templates'],
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

WSGI_APPLICATION = 'myproject.wsgi.application'

# ============================================
# データベース設定（.envファイルから読み込み）
# ============================================
# データベースタイプ（sqlite, local, rds）
# .envファイルで DB_TYPE=sqlite または DB_TYPE=local または DB_TYPE=rds を設定
# デフォルトはSQLite
DB_TYPE = os.environ.get("DB_TYPE", "sqlite")

# デバッグ: 使用するデータベースタイプを表示（本番環境では削除推奨）
if DEBUG:
    print(f"[DEBUG] DB_TYPE: {DB_TYPE}")

if DB_TYPE == "sqlite":
    # SQLiteでの接続（デフォルト）
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
elif DB_TYPE == "rds":
    # AWS RDS (PostgreSQL) での接続（.envファイルから読み込み）
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("RDS_DB_NAME"),
            "USER": os.environ.get("RDS_USERNAME"),
            "PASSWORD": os.environ.get("RDS_PASSWORD"),
            "HOST": os.environ.get("RDS_HOSTNAME"),
            "PORT": os.environ.get("RDS_PORT", "5432"),
            "OPTIONS": {
                "connect_timeout": int(os.environ.get("RDS_CONNECT_TIMEOUT", "10")),
            }
        }
    }
    # statement_timeoutが設定されている場合のみ追加
    if os.environ.get("RDS_STATEMENT_TIMEOUT"):
        DATABASES["default"]["OPTIONS"]["options"] = f"-c statement_timeout={os.environ.get('RDS_STATEMENT_TIMEOUT')}"
    
    # 必須環境変数のチェック（RDS用）
    required_env_vars = ["RDS_DB_NAME", "RDS_USERNAME", "RDS_PASSWORD", "RDS_HOSTNAME"]
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(
            f"以下の環境変数が設定されていません: {', '.join(missing_vars)}\n"
            f".envファイルを作成して、これらの値を設定してください。"
        )
else:
    # ローカルのPostgreSQLでの接続（.envファイルから読み込み）
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME"),
            "USER": os.environ.get("DB_USER"),
            "PASSWORD": os.environ.get("DB_PASSWORD"),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
    
    # 必須環境変数のチェック（ローカル用）
    required_env_vars = ["DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(
            f"以下の環境変数が設定されていません: {', '.join(missing_vars)}\n"
            f".envファイルを作成して、これらの値を設定してください。"
        )



STATIC_URL = '/static/'

# ============================================
# キャッシュ設定
# ============================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5分間キャッシュ
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}
STATICFILES_DIRS = [BASE_DIR / 'myapp' / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# Stripe決済設定
# ============================================
# 必要な情報：
# 1. Stripe公開可能キー（Publishable Key）
#    - Stripeダッシュボード > 開発者 > APIキー から取得
#    - 例: pk_test_51xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# 2. Stripeシークレットキー（Secret Key）
#    - Stripeダッシュボード > 開発者 > APIキー から取得
#    - 例: sk_test_51xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# 3. Stripe Webhookシークレット
#    - Stripeダッシュボード > 開発者 > Webhook でエンドポイント作成後、署名シークレットを取得
#    - 例: whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# 4. Stripe価格ID（Price ID）
#    - Stripeダッシュボード > 商品 > 価格 でProプランの価格を作成し、価格IDを取得
#    - 例: price_1xxxxxxxxxxxxxxxxxxxxxxxxx
#    - または、Planモデルにstripe_price_idフィールドを追加して管理

# Stripe APIキー（環境変数から取得）
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# Stripe価格ID（Proプラン）
STRIPE_PRO_PRICE_ID = os.environ.get('STRIPE_PRO_PRICE_ID', '')

# 決済成功後のリダイレクトURL
STRIPE_SUCCESS_URL = 'http://127.0.0.1:8000/checkout-success/'
STRIPE_CANCEL_URL = 'http://127.0.0.1:8000/pricing/'

# ============================================
# 認証設定（ポータル用）
# ============================================
# ポータル用のログインURL（未認証ユーザーがアクセスした場合のリダイレクト先）
LOGIN_URL = '/portal/login/'
# ログイン成功後のデフォルトリダイレクト先（ポータル用）
LOGIN_REDIRECT_URL = '/portal/'