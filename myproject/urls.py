from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),  # 管理者用管理画面（既存）
    path('portal/', include('portal.urls')),  # ユーザーポータル
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),
    path("", include("myapp.urls")),
]