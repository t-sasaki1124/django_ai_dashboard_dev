# Django AI Dashboard - YouTubeコメント管理ツール

このプロジェクトは、**DjangoベースのAIダッシュボード** です。  
YouTubeコメントをCSVからインポートし、管理画面で閲覧・分析・一括削除できるように構築されています。

---

## 🚀 1. 環境構築

### リポジトリをクローン
```bash
git clone https://github.com/<あなたのユーザー名>/django_ai_dashboard.git
cd django_ai_dashboard
```

### 仮想環境の作成と有効化

**Windows (PowerShell):**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 📦 2. 必要パッケージのインストール
```bash
pip install -r requirements.txt
```

もし `requirements.txt` がまだ無い場合は、以下を直接実行：
```bash
pip install django pandas matplotlib psycopg2-binary
```

### Stripe決済機能を使用する場合
```bash
pip install stripe
```

---

## 💳 Stripe決済機能の設定（オプション）

Proプランの決済にStripeを使用する場合、以下の設定が必要です。

### 1. Stripeアカウントの作成
1. [Stripe](https://stripe.com/jp) にアカウントを作成
2. ダッシュボードにログイン

### 2. APIキーの取得
1. Stripeダッシュボード > **開発者** > **APIキー** に移動
2. **公開可能キー（Publishable Key）** をコピー
   - 例: `pk_test_51xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
3. **シークレットキー（Secret Key）** をコピー
   - 例: `sk_test_51xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 3. 商品と価格の作成
1. Stripeダッシュボード > **商品** > **商品を追加** をクリック
2. 商品名: 「Proプラン」など
3. 価格を設定（例: ¥980/月）
4. 請求頻度: **毎月**
5. **価格ID（Price ID）** をコピー
   - 例: `price_1xxxxxxxxxxxxxxxxxxxxxxxxx`

### 4. Webhookエンドポイントの設定（本番環境用）
1. Stripeダッシュボード > **開発者** > **Webhook** に移動
2. **エンドポイントを追加** をクリック
3. エンドポイントURL: `https://yourdomain.com/stripe-webhook/`
4. イベントを選択:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. **署名シークレット（Signing secret）** をコピー
   - 例: `whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 5. settings.pyの設定
`myproject/settings.py` の以下の項目を設定：

```python
# Stripe APIキー
STRIPE_PUBLIC_KEY = 'pk_test_51xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
STRIPE_SECRET_KEY = 'sk_test_51xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
STRIPE_WEBHOOK_SECRET = 'whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# Stripe価格ID（Proプラン）
STRIPE_PRO_PRICE_ID = 'price_1xxxxxxxxxxxxxxxxxxxxxxxxx'

# 決済成功後のリダイレクトURL（本番環境では適宜変更）
STRIPE_SUCCESS_URL = 'http://127.0.0.1:8000/checkout-success/'
STRIPE_CANCEL_URL = 'http://127.0.0.1:8000/pricing/'
```

**⚠️ セキュリティ注意事項:**
- 本番環境では環境変数や `.env` ファイルから取得することを推奨
- シークレットキーは絶対にGitにコミットしないでください

### 6. PlanモデルにStripe価格IDを設定
1. Django管理画面にログイン
2. **プラン** > **Proプラン** を編集
3. **Stripe価格ID** フィールドに価格IDを入力
4. 保存

### 7. views.pyのコメントアウトを解除
`myapp/views.py` の以下の関数内のコメントアウトを解除：
- `create_checkout_session()`
- `checkout_success()`
- `stripe_webhook()`

### 8. 動作確認
1. `/pricing/` にアクセス
2. Proプランの **「今すぐアップグレード」** ボタンをクリック
3. Stripe Checkout画面にリダイレクトされることを確認

---

## ⚙️ 3. Django初期設定

### マイグレーションを実行
```bash
python manage.py migrate
```

### 管理ユーザーを作成
```bash
python manage.py createsuperuser
```
※ 以下を順に入力してください  
- ユーザー名  
- メールアドレス  
- パスワード  

---

## 🖥 4. サーバーを起動
```bash
venv\Scripts\activate
python manage.py runserver
```

ブラウザで以下にアクセス：
```
http://127.0.0.1:8000/admin/
```

ログイン画面が表示されたら、作成した管理者アカウントでログインします。

---

## 📁 5. YouTubeコメントのインポート

管理画面の手順：
1. 左メニューの **「YouTube Comments」** をクリック  
2. 画面上部の **「Import CSV」** ボタンをクリック  
3. CSVファイルを選択してアップロード  
4. アップロード後、コメント一覧にデータが表示されます  

CSVファイルの例：
```csv
id,video_id,comment_id,comment_text,author,like_count,reply_count,reply_depth_potential,engagement_score,created_at,ai_reply,embedding
1,PTw4q-pp1GE,Ugw2g3kQcoy9Sk2zRQh4AaABAg,"いい動画ですね！",@user1,5,0,0,0.8,2025-11-05 12:00:00,,
```

---

## 🗑 6. コメントの一括削除

コメントを全件削除するには：
- **「🗑 Delete All Comments」** ボタンをクリック  
- 成功すると以下のようなメッセージが表示されます：
  ```
  🗑 56 件のコメントを削除しました。
  ```

---

## 🧱 7. プロジェクト構成

```
django_ai_dashboard/
├─ myproject/
│  ├─ settings.py
│  ├─ urls.py(プロジェクト全体のURL)
│  └─ ...
├─ myapp/
│  ├─ admin.py
│  ├─ models.py
│  ├─ templates/
│  │   ├─ index.html
│  │   ├─ base.html
│  │   ├─ pricing.html
│  │   └─ admin/myapp/youtubecomment/change_list.html
│  ├─ static/
│  └─ ...
├─ db.sqlite3
├─ manage.py
└─ README.md
```

---

## 💡 8. よく使うコマンド集

| 目的 | コマンド |
|------|----------|
| サーバー起動 | `python manage.py runserver` |
| モデル変更を検知 | `python manage.py makemigrations` |
| DBに反映 | `python manage.py migrate` |
| 管理者作成 | `python manage.py createsuperuser` |
| エラーチェック | `python manage.py check` |
| 仮想環境終了 | `deactivate` |

---

## ⚠️ 9. 警告の対処法

以下の警告が出た場合：
```
staticfiles.W004: The directory 'myapp/static' does not exist.
```
→ `myapp/static` フォルダを手動で作成してください。
```bash
mkdir myapp/static
```

---

## 🔄 10. データをリセットしたい場合

すべてのコメントや設定を初期化したいとき：
```bash
del db.sqlite3
python manage.py migrate
```

---

## 📤 11. 変更をGitHubへ反映

```bash
git add .
git commit -m "Add CSV import and bulk delete features for YouTube comments in admin panel"
git push origin main
```

---

## ✅ 12. 動作確認

- `/admin/` にアクセスできる  
- CSVインポートが正常に行える  
- 「🗑 Delete All Comments」ボタンで全件削除できる  

---

## 🔐 13. ユーザーポータル機能

このプロジェクトには、**管理者用管理画面（Django Admin）**と**ユーザー用ポータル**の2つの管理画面が実装されています。

### 管理者用管理画面（Django Admin）

- **URL**: `/admin/`
- **アクセス制御**: `is_staff=True` のユーザーのみ
- **機能**: すべてのコメントを閲覧・編集・削除可能

### ユーザー用ポータル

- **URL**: `/portal/`
- **ログインURL**: `/portal/login/`
- **ログアウトURL**: `/portal/logout/`
- **アクセス制御**: ログイン必須（staffユーザーもアクセス可能）
- **機能**: ログインユーザーが所有するコメントのみを閲覧・編集・削除可能

#### ポータルの主な機能

1. **ダッシュボード** (`/portal/`)
   - コメント数の統計表示
   - 最近のコメント一覧

2. **コメント一覧** (`/portal/comments/`)
   - 自分のコメント一覧表示
   - 検索機能（コメント内容、投稿者、動画IDで検索）
   - ページネーション

3. **コメント詳細** (`/portal/comments/<id>/`)
   - コメントの詳細情報を表示

4. **コメント作成** (`/portal/comments/new/`)
   - 新しいコメントを作成（自動的に現在のユーザーがownerに設定）

5. **コメント編集** (`/portal/comments/<id>/edit/`)
   - 自分のコメントのみ編集可能（他人のコメントは404エラー）

6. **コメント削除** (`/portal/comments/<id>/delete/`)
   - 自分のコメントのみ削除可能（他人のコメントは404エラー）

#### セキュリティ機能

- **データ分離**: 各ユーザーは自分のコメントのみアクセス可能
- **所有者チェック**: 直接URLを入力しても他人のデータにはアクセスできない（404エラー）
- **CSRF保護**: すべてのフォームでCSRFトークン必須
- **認証必須**: 未ログインユーザーは自動的にログインページにリダイレクト

#### ポータルの使い方

1. **ユーザー作成**（管理者がDjango Adminで作成、または`createsuperuser`で作成）
2. **ポータルにアクセス**: `http://127.0.0.1:8000/portal/`
3. **ログイン**: 作成したユーザーでログイン
4. **コメント作成**: 「新規作成」ボタンからコメントを作成
5. **コメント管理**: 一覧・詳細・編集・削除が可能

#### 既存データの移行について

既存の`YouTubeComment`データに`owner`フィールドが追加されました。既存データの`owner`は`null`のままです。

- **ポータル側**: `owner`が`null`のコメントは表示されません（ユーザーは自分のコメントのみ表示）
- **管理者側**: `owner`が`null`のコメントも含めてすべてのコメントを表示・管理可能

既存データに`owner`を設定したい場合は、Django Adminから手動で設定するか、データ移行スクリプトを実行してください。

---

## 🧠 補足メモ

- 現状はSQLiteを使用（`db.sqlite3`）  
- 今後PostgreSQLやAI分析機能に拡張可能  
- 静的ファイル (`/static`) にCSS・グラフ画像を配置可能  
- **ユーザーポータル機能**: ユーザーが自分のデータのみ操作できる管理画面を提供

---

## 📋 14. 実装ファイル一覧

### 新規作成されたファイル

#### portalアプリ
- `portal/__init__.py`
- `portal/admin.py`
- `portal/apps.py`
- `portal/models.py`
- `portal/tests.py`
- `portal/views.py`
- `portal/urls.py`
- `portal/forms.py` - コメント用フォーム
- `portal/mixins.py` - 認証・認可用Mixin
- `portal/templates/portal/base.html` - ベーステンプレート
- `portal/templates/portal/login.html` - ログインテンプレート
- `portal/templates/portal/dashboard.html` - ダッシュボード
- `portal/templates/portal/comment_list.html` - コメント一覧
- `portal/templates/portal/comment_detail.html` - コメント詳細
- `portal/templates/portal/comment_form.html` - コメント作成・編集フォーム
- `portal/templates/portal/comment_confirm_delete.html` - 削除確認

### 変更されたファイル

- `myapp/models.py` - `YouTubeComment`モデルに`owner`フィールドを追加
- `myapp/admin.py` - `YouTubeCommentAdmin`に`owner`フィールドを追加
- `myproject/settings.py` - `portal`アプリを追加、認証設定を追加
- `myproject/urls.py` - `/portal/`のURLルーティングを追加

### マイグレーションファイル

- `myapp/migrations/0007_youtubecomment_owner_alter_plan_stripe_price_id.py` - `owner`フィールド追加のマイグレーション

---

## 🔗 15. URL一覧

### 管理者用（Django Admin）
- `/admin/` - 管理画面トップ
- `/admin/myapp/youtubecomment/` - コメント一覧（管理者用）

### ユーザー用ポータル
- `/portal/` - ダッシュボード
- `/portal/login/` - ログイン
- `/portal/logout/` - ログアウト
- `/portal/comments/` - コメント一覧
- `/portal/comments/new/` - コメント作成
- `/portal/comments/<id>/` - コメント詳細
- `/portal/comments/<id>/edit/` - コメント編集
- `/portal/comments/<id>/delete/` - コメント削除

---

## 🚀 16. 動作確認手順

### 1. マイグレーション実行
```bash
python manage.py migrate
```

### 2. サーバー起動
```bash
python manage.py runserver
```

### 3. 管理者用管理画面の確認
1. `http://127.0.0.1:8000/admin/` にアクセス
2. 管理者アカウントでログイン
3. 「YouTube Comments」を確認（`owner`フィールドが追加されていることを確認）

### 4. ユーザー用ポータルの確認
1. `http://127.0.0.1:8000/portal/` にアクセス
2. ログインページにリダイレクトされることを確認
3. ユーザーアカウントでログイン（管理者アカウントでも可）
4. ダッシュボードが表示されることを確認
5. 「新規作成」からコメントを作成
6. 作成したコメントが一覧に表示されることを確認
7. コメントの詳細・編集・削除が正常に動作することを確認

### 5. セキュリティ確認
1. ユーザーAでログインしてコメントを作成
2. ログアウト
3. ユーザーBでログイン
4. ユーザーAのコメントのURL（`/portal/comments/<id>/`）に直接アクセス
5. 404エラーが表示されることを確認（他人のデータにアクセスできない）

---

© 2025 ts  
Built with using **Django 4.2**
