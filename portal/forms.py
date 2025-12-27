"""
ポータル用のフォーム
"""
from django import forms
from myapp.models import YouTubeComment


class YouTubeCommentForm(forms.ModelForm):
    """
    YouTubeComment用のフォーム
    """
    class Meta:
        model = YouTubeComment
        fields = [
            'video_id',
            'comment_id',
            'comment_text',
            'author',
            'like_count',
            'reply_count',
            'created_at',
            'reply_depth_potential',
            'engagement_score',
            'ai_reply',
        ]
        widgets = {
            'video_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例: dQw4w9WgXcQ'
            }),
            'comment_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'コメントID'
            }),
            'comment_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'コメント内容を入力してください'
            }),
            'author': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '投稿者名'
            }),
            'like_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'reply_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'created_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'reply_depth_potential': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'engagement_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': 0
            }),
            'ai_reply': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'AI返信内容（オプション）'
            }),
        }
        labels = {
            'video_id': '動画ID',
            'comment_id': 'コメントID',
            'comment_text': 'コメント内容',
            'author': '投稿者',
            'like_count': 'いいね数',
            'reply_count': '返信数',
            'created_at': '作成日時',
            'reply_depth_potential': '返信深度',
            'engagement_score': 'エンゲージメントスコア',
            'ai_reply': 'AI返信',
        }

