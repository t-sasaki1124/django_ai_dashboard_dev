"""
ポータル用のビュー
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from myapp.models import YouTubeComment
from .forms import YouTubeCommentForm
from .mixins import PortalLoginRequiredMixin, OwnerRequiredMixin


class PortalLoginView(LoginView):
    """
    ポータル用のログインビュー
    """
    template_name = 'portal/login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """
        ログイン成功後のリダイレクト先
        """
        next_url = self.request.GET.get('next', '/portal/')
        return next_url
    
    def form_valid(self, form):
        """
        ログイン成功時の処理
        """
        return super().form_valid(form)


class PortalLogoutView(LogoutView):
    """
    ポータル用のログアウトビュー
    """
    next_page = '/portal/login/'
    
    def dispatch(self, request, *args, **kwargs):
        """
        ログアウト時の処理
        """
        return super().dispatch(request, *args, **kwargs)


class PortalDashboardView(PortalLoginRequiredMixin, ListView):
    """
    ポータルダッシュボード（一覧ページ）
    """
    template_name = 'portal/dashboard.html'
    context_object_name = 'comments'
    paginate_by = 20
    
    def get_queryset(self):
        """
        ログインユーザーの所有するコメントのみを取得
        """
        queryset = YouTubeComment.objects.filter(owner=self.request.user)
        
        # 検索機能
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(comment_text__icontains=search_query) |
                Q(author__icontains=search_query) |
                Q(video_id__icontains=search_query)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """
        コンテキストデータに追加情報を設定
        """
        context = super().get_context_data(**kwargs)
        context['total_count'] = YouTubeComment.objects.filter(owner=self.request.user).count()
        context['search_query'] = self.request.GET.get('search', '')
        return context


class CommentListView(PortalLoginRequiredMixin, OwnerRequiredMixin, ListView):
    """
    コメント一覧ビュー
    """
    model = YouTubeComment
    template_name = 'portal/comment_list.html'
    context_object_name = 'comments'
    paginate_by = 20
    
    def get_queryset(self):
        """
        ログインユーザーの所有するコメントのみを取得
        """
        queryset = super().get_queryset()
        
        # 検索機能
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(comment_text__icontains=search_query) |
                Q(author__icontains=search_query) |
                Q(video_id__icontains=search_query)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """
        コンテキストデータに追加情報を設定
        """
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class CommentDetailView(PortalLoginRequiredMixin, OwnerRequiredMixin, DetailView):
    """
    コメント詳細ビュー
    """
    model = YouTubeComment
    template_name = 'portal/comment_detail.html'
    context_object_name = 'comment'


class CommentCreateView(PortalLoginRequiredMixin, CreateView):
    """
    コメント作成ビュー
    """
    model = YouTubeComment
    form_class = YouTubeCommentForm
    template_name = 'portal/comment_form.html'
    success_url = reverse_lazy('portal:comment_list')
    
    def form_valid(self, form):
        """
        フォームが有効な場合、ownerを現在のユーザーに設定
        """
        form.instance.owner = self.request.user
        messages.success(self.request, 'コメントを作成しました。')
        return super().form_valid(form)


class CommentUpdateView(PortalLoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    """
    コメント更新ビュー
    """
    model = YouTubeComment
    form_class = YouTubeCommentForm
    template_name = 'portal/comment_form.html'
    success_url = reverse_lazy('portal:comment_list')
    
    def form_valid(self, form):
        """
        フォームが有効な場合の処理
        """
        messages.success(self.request, 'コメントを更新しました。')
        return super().form_valid(form)


class CommentDeleteView(PortalLoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    """
    コメント削除ビュー
    """
    model = YouTubeComment
    template_name = 'portal/comment_confirm_delete.html'
    success_url = reverse_lazy('portal:comment_list')
    context_object_name = 'comment'
    
    def delete(self, request, *args, **kwargs):
        """
        削除時の処理
        """
        messages.success(request, 'コメントを削除しました。')
        return super().delete(request, *args, **kwargs)
