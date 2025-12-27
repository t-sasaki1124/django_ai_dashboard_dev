from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("pricing/", views.pricing, name="pricing"),
    path("comments-table/", views.comments_table, name="comments_table"),
    # CSV/JSONインポート
    path("import-csv/", views.import_csv, name="import_csv"),
    path("import-json/", views.import_json, name="import_json"),
    # プラン変更
    path("downgrade-to-free/", views.downgrade_to_free, name="downgrade_to_free"),
    # Stripe決済関連
    path("create-checkout-session/<int:plan_id>/", views.create_checkout_session, name="create_checkout_session"),
    path("checkout-success/", views.checkout_success, name="checkout_success"),
    path("stripe-webhook/", views.stripe_webhook, name="stripe_webhook"),
]
