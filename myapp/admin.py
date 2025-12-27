from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import path
from django.http import HttpResponse
from django.utils.html import format_html
from .models import YouTubeComment, UserProfile, Plan, UserPlan
import csv
from io import TextIOWrapper
from datetime import datetime, timedelta

# 管理画面のタイトルをカスタマイズ
admin.site.site_header = "Management Console"
admin.site.site_title = "Management Console"
admin.site.index_title = ""  # インデックスページのタイトルを空に（ヘッダーと重複しないように）

# UserAdminのフィルター機能を削除
class UserAdmin(BaseUserAdmin):
    list_filter = ()  # フィルター機能を削除

# 既存のUserAdminを登録解除して、カスタムUserAdminを登録
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'price', 'is_premium', 'created_at')
    list_filter = ()  # フィルター機能を削除
    search_fields = ('display_name', 'name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'display_name', 'price', 'is_premium', 'description')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserPlan)
class UserPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'is_active', 'started_at', 'expires_at', 'is_premium_display')
    list_filter = ()  # フィルター機能を削除
    search_fields = ('user__username', 'user__email', 'plan__display_name')
    readonly_fields = ('created_at', 'updated_at', 'is_premium_display')
    fieldsets = (
        ('ユーザー情報', {
            'fields': ('user', 'plan')
        }),
        ('プラン情報', {
            'fields': ('is_active', 'started_at', 'expires_at', 'is_premium_display')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_premium_display(self, obj):
        return obj.is_premium
    is_premium_display.short_description = '有料プラン'
    is_premium_display.boolean = True

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # 新規作成時、URLパラメータからユーザーとプランを設定
        if not obj and request.GET.get('user_id'):
            try:
                from django.contrib.auth.models import User
                from .models import Plan
                user = User.objects.get(id=request.GET.get('user_id'))
                form.base_fields['user'].initial = user
                if request.GET.get('plan_id'):
                    plan = Plan.objects.get(id=request.GET.get('plan_id'))
                    form.base_fields['plan'].initial = plan
            except:
                pass
        # 編集時、URLパラメータからプランを設定
        elif obj and request.GET.get('plan_id'):
            try:
                plan = Plan.objects.get(id=request.GET.get('plan_id'))
                form.base_fields['plan'].initial = plan
            except:
                pass
        return form

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        # 編集時にURLパラメータでプランIDが渡された場合、自動的にプランを変更
        if object_id and request.GET.get('plan_id'):
            try:
                user_plan = UserPlan.objects.get(id=object_id)
                plan = Plan.objects.get(id=request.GET.get('plan_id'))
                user_plan.plan = plan
                user_plan.save()
                messages.success(request, f'プランを "{plan.display_name}" に変更しました。')
                from django.shortcuts import redirect
                return redirect('admin:myapp_userplan_changelist')
            except:
                pass
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_premium', 'created_at', 'updated_at')
    list_filter = ()  # フィルター機能を削除
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(YouTubeComment)
class YouTubeCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'owner', 'like_count', 'reply_count', 'created_at')
    list_filter = ('owner', 'created_at')
    search_fields = ('author', 'comment_text', 'video_id', 'owner__username')
    readonly_fields = ('id',)
    fieldsets = (
        ('基本情報', {
            'fields': ('video_id', 'comment_id', 'comment_text', 'author')
        }),
        ('統計情報', {
            'fields': ('like_count', 'reply_count', 'reply_depth_potential', 'engagement_score')
        }),
        ('その他', {
            'fields': ('created_at', 'ai_reply', 'embedding', 'owner')
        }),
    )
    change_list_template = "admin/myapp/youtubecomment/change_list.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        # 有料プランチェック（新しいUserPlanモデルを使用）
        is_premium = False
        current_plan = None
        if request.user.is_authenticated:
            try:
                user_plan = UserPlan.objects.get(user=request.user, is_active=True)
                is_premium = user_plan.is_premium
                current_plan = user_plan.plan
            except UserPlan.DoesNotExist:
                # UserPlanが存在しない場合は、デフォルトで無料プラン
                pass
        extra_context['is_premium'] = is_premium
        extra_context['current_plan'] = current_plan
        return super().changelist_view(request, extra_context=extra_context)

    # ✅ URLルーティング追加
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.import_csv, name='import_csv'),
            path('delete-all/', self.delete_all, name='delete_all_youtube_comments'),
            path('export-report/', self.export_report, name='export_report'),
        ]
        return custom_urls + urls

    # ✅ CSVインポート機能
    def import_csv(self, request):
        if request.method == "POST" and request.FILES.get("csv_file"):
            csv_file = TextIOWrapper(request.FILES["csv_file"].file, encoding="utf-8")
            reader = csv.DictReader(csv_file)
            count = 0
            for row in reader:
                YouTubeComment.objects.create(
                    video_id=row.get("video_id"),
                    comment_id=row.get("comment_id"),
                    comment_text=row.get("comment_text"),
                    author=row.get("author"),
                    like_count=int(row.get("like_count") or 0),
                    reply_count=int(row.get("reply_count") or 0),
                    reply_depth_potential=int(row.get("reply_depth_potential") or 0),
                    engagement_score=float(row.get("engagement_score") or 0),
                    created_at=row.get("created_at") or None,
                    ai_reply=row.get("ai_reply") if row.get("ai_reply") != "null" else None,
                    embedding=row.get("embedding") if row.get("embedding") else None,
                )
                count += 1
            messages.success(request, f"{count} 件のコメントをインポートしました。")
            return redirect("..")

        messages.error(request, "CSVファイルを選択してください。")
        return redirect("..")

    # ✅ 全件削除機能（CSVと同じレベルに定義）
    def delete_all(self, request):
        count = YouTubeComment.objects.count()
        YouTubeComment.objects.all().delete()
        messages.success(request, f"{count} 件のコメントを削除しました。")
        return redirect("..")

    # ✅ レポート出力機能（有料プランのみ）
    def export_report(self, request):
        # 有料プランチェック（新しいUserPlanモデルを使用）
        if not request.user.is_authenticated:
            messages.error(request, "ログインが必要です。")
            return redirect("..")
        
        # ユーザープランを取得
        try:
            user_plan = UserPlan.objects.get(user=request.user, is_active=True)
            if not user_plan.is_premium:
                messages.error(request, "この機能は有料プランのみ利用可能です。")
                return redirect("..")
        except UserPlan.DoesNotExist:
            messages.error(request, "この機能は有料プランのみ利用可能です。")
            return redirect("..")
        
        # CSVレポートを生成
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="youtube_comments_report_{timestamp}.csv"'
        
        writer = csv.writer(response)
        
        # ヘッダー行
        writer.writerow([
            'ID', 'Video ID', 'Comment ID', 'Author', 'Comment Text',
            'Like Count', 'Reply Count', 'Engagement Score',
            'Reply Depth Potential', 'Created At', 'AI Reply'
        ])
        
        # データ行
        comments = YouTubeComment.objects.all().order_by('-created_at')
        for comment in comments:
            writer.writerow([
                comment.id,
                comment.video_id,
                comment.comment_id,
                comment.author,
                comment.comment_text,
                comment.like_count,
                comment.reply_count,
                comment.engagement_score,
                comment.reply_depth_potential,
                comment.created_at.strftime('%Y-%m-%d %H:%M:%S') if comment.created_at else '',
                comment.ai_reply or '',
            ])
        
        messages.success(request, f"レポートを出力しました（{comments.count()}件）。")
        return response
