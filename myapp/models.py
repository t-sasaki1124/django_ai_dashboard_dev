from django.db import models
from django.contrib.auth.models import User

class YouTubeComment(models.Model):
    video_id = models.CharField(max_length=50)
    comment_id = models.CharField(max_length=50)
    comment_text = models.TextField()
    author = models.CharField(max_length=100)
    like_count = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(null=True, blank=True)
    reply_depth_potential = models.IntegerField(default=0)
    engagement_score = models.FloatField(default=0)
    ai_reply = models.TextField(null=True, blank=True)
    embedding = models.TextField(null=True, blank=True)
    # ポータル用: コメントの所有者（ユーザーが自分のデータのみ操作可能にするため）
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='youtube_comments', null=True, blank=True, verbose_name="所有者")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "YouTube Comment"
        verbose_name_plural = "YouTube Comments"

    def __str__(self):
        return f"{self.author}: {self.comment_text[:40]}..."


class Plan(models.Model):
    """プランモデル - プランの種類を定義"""
    PLAN_CHOICES = [
        ('free', '無料プラン'),
        ('pro', 'Proプラン'),
        ('enterprise', 'Enterpriseプラン'),
    ]
    
    name = models.CharField(max_length=50, unique=True, choices=PLAN_CHOICES, verbose_name="プラン名")
    display_name = models.CharField(max_length=100, verbose_name="表示名")
    price = models.IntegerField(default=0, verbose_name="価格（円/月）")
    is_premium = models.BooleanField(default=False, verbose_name="有料プラン")
    description = models.TextField(blank=True, verbose_name="説明")
    # Stripeの価格ID
    stripe_price_id = models.CharField(max_length=200, blank=True, null=True, verbose_name="Stripe価格ID", help_text="price_1SaoNrHKU8SnCbsFH2ObkYS4")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "プラン"
        verbose_name_plural = "プラン"

    def __str__(self):
        return self.display_name


class UserPlan(models.Model):
    """ユーザープランモデル - ユーザーとプランの紐付け"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_plan')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, related_name='users', verbose_name="プラン")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="開始日時")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="有効期限")
    is_active = models.BooleanField(default=True, verbose_name="有効")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ユーザープラン"
        verbose_name_plural = "ユーザープラン"

    def __str__(self):
        plan_name = self.plan.display_name if self.plan else "未設定"
        return f"{self.user.username} - {plan_name}"

    @property
    def is_premium(self):
        """有料プランかどうかを返す"""
        return self.plan and self.plan.is_premium and self.is_active


class UserProfile(models.Model):
    """ユーザープロファイル - 有料プラン情報を管理（後方互換性のため残す）"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_premium = models.BooleanField(default=False, verbose_name="有料プラン")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ユーザープロファイル"
        verbose_name_plural = "ユーザープロファイル"

    def __str__(self):
        return f"{self.user.username} - {'有料' if self.is_premium else '無料'}"
