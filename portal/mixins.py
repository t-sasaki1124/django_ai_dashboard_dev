"""
ポータル用の認証・認可Mixin
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.http import Http404


class PortalLoginRequiredMixin(LoginRequiredMixin):
    """
    ポータル用のログイン必須Mixin
    staffユーザーもポータルにアクセス可能（設計判断: 管理者もポータルを確認できるようにする）
    """
    login_url = '/portal/login/'
    redirect_field_name = 'next'


class OwnerRequiredMixin:
    """
    オブジェクトの所有者のみアクセス可能にするMixin
    存在しない場合は404を返す（セキュリティのため、403ではなく404）
    """
    owner_field = 'owner'  # 所有者フィールド名
    
    def get_queryset(self):
        """
        ログインユーザーの所有するオブジェクトのみを返す
        """
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated:
            return queryset.none()
        return queryset.filter(**{self.owner_field: self.request.user})
    
    def get_object(self, queryset=None):
        """
        オブジェクトを取得し、所有者チェックを行う
        所有者でない場合は404を返す
        """
        obj = super().get_object(queryset)
        owner = getattr(obj, self.owner_field, None)
        
        # ownerがNoneの場合は、既存データの可能性があるため、ログインユーザーに割り当てる
        if owner is None:
            # 既存データの移行用: ownerがNoneの場合は現在のユーザーに割り当て
            # 本番環境では適切な移行スクリプトを実行すること
            if self.request.user.is_authenticated:
                setattr(obj, self.owner_field, self.request.user)
                obj.save(update_fields=[self.owner_field])
                return obj
        
        # 所有者チェック
        if owner != self.request.user:
            raise Http404("このリソースは存在しません。")
        
        return obj

