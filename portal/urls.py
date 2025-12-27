"""
ポータル用のURL設定
"""
from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    # 認証関連
    path('login/', views.PortalLoginView.as_view(), name='login'),
    path('logout/', views.PortalLogoutView.as_view(), name='logout'),
    
    # ダッシュボード
    path('', views.PortalDashboardView.as_view(), name='dashboard'),
    
    # コメントCRUD
    path('comments/', views.CommentListView.as_view(), name='comment_list'),
    path('comments/new/', views.CommentCreateView.as_view(), name='comment_create'),
    path('comments/<int:pk>/', views.CommentDetailView.as_view(), name='comment_detail'),
    path('comments/<int:pk>/edit/', views.CommentUpdateView.as_view(), name='comment_update'),
    path('comments/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),
]

