from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.cache import cache
from django.db.models import Max, Count
from .models import YouTubeComment, Plan, UserPlan
import json
import pandas as pd
import csv
from io import TextIOWrapper
from datetime import datetime
import numpy as np
import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
try:
    from janome.tokenizer import Tokenizer
    JANOME_AVAILABLE = True
except ImportError:
    JANOME_AVAILABLE = False


def clean_text(text):
    """Basic text cleaning: URLs, mentions, excessive symbols."""
    if pd.isna(text):
        return ""
    
    text = str(text)
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    # Remove mentions (e.g., @username)
    text = re.sub(r'@\w+', '', text)
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove excessive symbols (keep basic punctuation)
    text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
    return text.strip()


def extract_japanese_words(text):
    """Extract meaningful Japanese words using morphological analysis."""
    if not text:
        return []
    
    # Remove URLs, mentions, and clean text
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    
    words = []
    
    if JANOME_AVAILABLE:
        try:
            tokenizer = Tokenizer()
            tokens = tokenizer.tokenize(text)
            
            # Filter stop words and extract meaningful words
            stop_words = {'の', 'に', 'は', 'を', 'が', 'で', 'と', 'も', 'か', 'な', 'だ', 'です', 'ます', 'ました', 'て', 'た', 'する', 'した', 'ある', 'いる', 'なる', 'れる', 'られる', 'です', 'ます', 'でした', 'ました', 'です', 'ます', 'です', 'ます'}
            stop_pos = ['助詞', '助動詞', '記号']
            
            for token in tokens:
                surface = token.surface
                pos = token.part_of_speech.split(',')[0]
                
                # Skip stop words and stop parts of speech
                if surface not in stop_words and pos not in stop_pos:
                    # Keep nouns, verbs, adjectives, and meaningful words
                    if pos in ['名詞', '動詞', '形容詞'] or len(surface) >= 2:
                        if len(surface) >= 2 and len(surface) <= 10:
                            words.append(surface)
        except Exception:
            # Fallback to simple extraction if tokenization fails
            pass
    
    # Fallback: simple character-based extraction
    if not words:
        japanese_pattern = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\w]+'
        phrases = re.findall(japanese_pattern, text)
        stop_words = {'の', 'に', 'は', 'を', 'が', 'で', 'と', 'も', 'か', 'な', 'だ', 'です', 'ます', 'ました', 'て', 'た', 'する', 'した', 'ある', 'いる', 'なる', 'れる', 'られる'}
        words = [p for p in phrases if 2 <= len(p) <= 10 and p not in stop_words]
    
    return words


def analyze_cluster_features(comments, cluster_labels, vectorizer, n_clusters):
    """Analyze features of each cluster and generate summary."""
    cluster_analyses = []
    
    # Get feature names from vectorizer
    feature_names = vectorizer.get_feature_names_out()
    
    for i in range(n_clusters):
        mask = np.array(cluster_labels) == i
        cluster_comments = [comments[j] for j in range(len(comments)) if mask[j]]
        
        if len(cluster_comments) == 0:
            continue
        
        # Extract meaningful words from comments using morphological analysis
        all_words = []
        for comment in cluster_comments:
            words = extract_japanese_words(comment)
            all_words.extend(words)
        
        # Count word frequency
        word_freq = Counter(all_words)
        
        # Get top keywords: combine TF-IDF and frequency-based approach
        # First, get TF-IDF top keywords
        cluster_text = ' '.join(cluster_comments)
        cluster_vector = vectorizer.transform([cluster_text])
        feature_array = cluster_vector.toarray()[0]
        top_indices = np.argsort(feature_array)[-15:][::-1]  # Top 15 keywords
        tfidf_keywords = [feature_names[idx] for idx in top_indices if feature_array[idx] > 0]
        
        # Get top frequent words (at least 2 occurrences)
        frequent_words = [word for word, count in word_freq.most_common(20) if count >= 2]
        
        # Combine and deduplicate, prioritize frequent words
        combined_keywords = []
        seen = set()
        
        # Add frequent words first (they are more reliable)
        for word in frequent_words[:5]:
            if word not in seen and len(word) >= 2:
                combined_keywords.append(word)
                seen.add(word)
        
        # Add TF-IDF keywords that aren't already included
        for keyword in tfidf_keywords:
            if keyword not in seen and len(keyword) >= 2:
                combined_keywords.append(keyword)
                seen.add(keyword)
        
        # Get top 3 keywords
        top_keywords = combined_keywords[:3]
        
        # Generate summary
        avg_length = np.mean([len(c) for c in cluster_comments])
        sample_comments = cluster_comments[:3]  # Sample comments
        
        cluster_analyses.append({
            'cluster_id': i,
            'comment_count': len(cluster_comments),
            'top_keywords': top_keywords,  # Top 3 keywords (unified)
            'avg_comment_length': round(avg_length, 1),
            'sample_comments': sample_comments
        })
    
    return cluster_analyses


def perform_clustering(comments_df, n_clusters=6):
    """Perform 3D clustering on comments."""
    if comments_df is None or len(comments_df) == 0:
        return None
    
    # Check if comment_text column exists
    if 'comment_text' not in comments_df.columns:
        return None
    
    try:
        # Extract and clean comments
        comments = comments_df['comment_text'].apply(clean_text).tolist()
        comments = [c for c in comments if c and len(c.strip()) > 0]  # Remove empty comments
        
        # Limit max clusters to 6
        max_clusters = min(6, n_clusters)
        if len(comments) < max_clusters:
            max_clusters = max(2, len(comments) // 2)
        
        if len(comments) < 2:
            return None
        
        # Vectorize
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        vectors = vectorizer.fit_transform(comments)
        
        if vectors.shape[0] < 2:
            return None
        
        # Reduce to 3D
        pca = PCA(n_components=3, random_state=42)
        vectors_3d = pca.fit_transform(vectors.toarray())
        
        # Cluster
        kmeans = KMeans(n_clusters=max_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(vectors_3d)
        
        # Analyze cluster features
        cluster_analyses = analyze_cluster_features(comments, cluster_labels.tolist(), vectorizer, max_clusters)
        
        # Calculate cluster centers and radii for sphere visualization
        cluster_centers = []
        cluster_radii = []
        for i in range(max_clusters):
            mask = cluster_labels == i
            if np.sum(mask) > 0:
                cluster_points = vectors_3d[mask]
                center = np.mean(cluster_points, axis=0)
                # Calculate radius as max distance from center to points in cluster
                distances = np.linalg.norm(cluster_points - center, axis=1)
                radius = np.max(distances) if len(distances) > 0 else 0.1
                cluster_centers.append(center.tolist())
                cluster_radii.append(float(radius))
            else:
                cluster_centers.append([0, 0, 0])
                cluster_radii.append(0.1)
        
        # Add jitter to points to prevent overlapping
        # Calculate the overall scale of the data
        data_range = np.max(vectors_3d, axis=0) - np.min(vectors_3d, axis=0)
        jitter_scale = np.mean(data_range) * 0.02  # 2% of average range
        
        # Add small random offset to each point
        np.random.seed(42)  # For reproducibility
        jitter = np.random.normal(0, jitter_scale, vectors_3d.shape)
        vectors_3d_jittered = vectors_3d + jitter
        
        # Prepare data for visualization
        cluster_data = {
            'x': vectors_3d_jittered[:, 0].tolist(),
            'y': vectors_3d_jittered[:, 1].tolist(),
            'z': vectors_3d_jittered[:, 2].tolist(),
            'cluster_labels': cluster_labels.tolist(),
            'comments': comments,
            'explained_variance': float(pca.explained_variance_ratio_.sum()),
            'n_clusters': max_clusters,
            'cluster_centers': cluster_centers,
            'cluster_radii': cluster_radii,
            'cluster_analyses': cluster_analyses
        }
        
        return cluster_data
    except Exception as e:
        import traceback
        print(f"Clustering error: {e}")
        print(traceback.format_exc())
        return None


def index(request):
    # 表示件数をクエリパラメータから取得（デフォルト: 30件）
    limit_options = [10, 30, 50]
    limit = int(request.GET.get('limit', 30))
    if limit not in limit_options:
        limit = 30
    
    # ページ番号を取得（デフォルト: 1ページ目）
    page_number = request.GET.get('page', 1)
    
    # テーブル表示用には全件を取得してページネーション
    all_comments = YouTubeComment.objects.all().order_by('-created_at')
    
    # ページネーション
    paginator = Paginator(all_comments, limit)
    page_obj = paginator.get_page(page_number)
    comments = page_obj.object_list

    # キャッシュキー生成用：データが更新されたかどうかを判定
    # コメント数と最新更新時刻を取得
    comment_count = YouTubeComment.objects.count()
    latest_update = YouTubeComment.objects.aggregate(Max('created_at'))['created_at__max']
    cache_key_base = f"index_data_{comment_count}_{latest_update}"
    
    # キャッシュからデータを取得
    graph_data = cache.get(f"{cache_key_base}_graph")
    stats = cache.get(f"{cache_key_base}_stats")
    analysis = cache.get(f"{cache_key_base}_analysis")
    advice = cache.get(f"{cache_key_base}_advice")
    cluster_data = cache.get(f"{cache_key_base}_cluster")
    
    # キャッシュにない場合は計算
    if graph_data is None or stats is None:
        # グラフ用には最大300件を使用
        comments_for_graph = YouTubeComment.objects.all()[:300]
        
        if comments_for_graph.exists():
            df = pd.DataFrame(list(comments_for_graph.values(
            "like_count",
            "reply_count",
            "created_at",
                "author",
                "comment_text",
            )))

            # タイムスタンプを数値に変換
            df["created_at_num"] = df["created_at"].astype("int64") // 10**9
            
            # グラフ用のデータをリスト形式に変換
            graph_data = {
                "x": df["like_count"].tolist(),
                "y": df["reply_count"].tolist(),
                "z": df["created_at_num"].tolist(),
                "text": [
                    f"Author: {author}<br>Likes: {likes}<br>Replies: {replies}<br>Comment: {text[:50]}..."
                    for author, likes, replies, text in zip(
                        df["author"], df["like_count"], df["reply_count"], df["comment_text"]
                    )
                ],
                "colors": df["created_at_num"].tolist(),  # 色分け用
            }

            # 統計情報を計算
            stats = {
                "total_comments": len(df),
                "avg_likes": float(df["like_count"].mean()),
                "avg_replies": float(df["reply_count"].mean()),
                "max_likes": int(df["like_count"].max()),
                "max_replies": int(df["reply_count"].max()),
                "total_likes": int(df["like_count"].sum()),
                "total_replies": int(df["reply_count"].sum()),
            }
            
            # 分析結果とアドバイスを生成（有料プラン・無料プラン両方で生成）
            if analysis is None:
                analysis = None
                advice = None
            
            if len(df) > 0:
                # 分析結果を生成
                high_engagement = df[(df["like_count"] > stats["avg_likes"]) & (df["reply_count"] > stats["avg_replies"])]
                low_engagement = df[(df["like_count"] < stats["avg_likes"]) & (df["reply_count"] < stats["avg_replies"])]
                
                engagement_ratio = len(high_engagement) / len(df) * 100 if len(df) > 0 else 0
                
                analysis = {
                    "high_engagement_count": len(high_engagement),
                    "low_engagement_count": len(low_engagement),
                    "engagement_ratio": round(engagement_ratio, 1),
                    "top_comment_likes": int(df.nlargest(1, "like_count")["like_count"].iloc[0]) if len(df) > 0 else 0,
                    "top_comment_replies": int(df.nlargest(1, "reply_count")["reply_count"].iloc[0]) if len(df) > 0 else 0,
                }
                
                # アドバイスを生成
                advice_items = []
                
                if stats["avg_likes"] < 5:
                    advice_items.append("平均いいね数が低い傾向にあります。コメントの内容をより具体的で価値のあるものにすることで、エンゲージメントを向上させることができます。")
                
                if stats["avg_replies"] < 2:
                    advice_items.append("返信数が少ない傾向にあります。質問形式のコメントや議論を促す内容を増やすことで、コミュニティの活性化につながります。")
                
                if engagement_ratio < 20:
                    advice_items.append("高エンゲージメントコメントの割合が低いです。視聴者の興味を引く話題や、タイムリーな内容を意識することで改善できます。")
                
                if len(high_engagement) > 0:
                    top_comment = df.nlargest(1, "like_count").iloc[0]
                    advice_items.append(f"最もエンゲージメントが高いコメントは{int(top_comment['like_count'])}いいね、{int(top_comment['reply_count'])}返信を獲得しています。このようなコメントの特徴を分析し、同様のアプローチを他のコメントにも適用することをお勧めします。")
                
                if stats["max_likes"] > stats["avg_likes"] * 3:
                    advice_items.append("一部のコメントが非常に高いエンゲージメントを獲得しています。これらの成功パターンを分析し、コンテンツ戦略に反映させることで、全体的なエンゲージメント向上が期待できます。")
                
                if not advice_items:
                    advice_items.append("現在のエンゲージメント状況は良好です。継続的な分析と改善により、さらなる成長が期待できます。")
                
                advice = advice_items
            
            # 3Dクラスタリング処理
            if cluster_data is None:
                cluster_data = None
                if len(df) > 0:
                    try:
                        cluster_data = perform_clustering(df, n_clusters=6)
                    except Exception as e:
                        import traceback
                        print(f"Clustering failed: {e}")
                        print(traceback.format_exc())
                        cluster_data = None
            
            # キャッシュに保存（5分間有効）
            cache.set(f"{cache_key_base}_graph", graph_data, 300)
            cache.set(f"{cache_key_base}_stats", stats, 300)
            cache.set(f"{cache_key_base}_analysis", analysis, 300)
            cache.set(f"{cache_key_base}_advice", advice, 300)
            if cluster_data:
                cache.set(f"{cache_key_base}_cluster", cluster_data, 300)
        else:
            # comments_for_graphが存在しない場合の初期化
            if cluster_data is None:
                cluster_data = None
    
    # 有料プランチェック（ユーザーごとに異なるためキャッシュしない）
    is_premium = False
    if request.user.is_authenticated:
        try:
            user_plan = UserPlan.objects.get(user=request.user, is_active=True)
            is_premium = user_plan.is_premium
        except UserPlan.DoesNotExist:
            pass

    return render(request, "index.html", {
        "graph_data": json.dumps(graph_data) if graph_data else None,
        "stats": stats,
        "comments": comments,
        "page_obj": page_obj,
        "current_limit": limit,
        "limit_options": limit_options,
        "is_premium": is_premium,
        "analysis": analysis,
        "advice": advice,
        "cluster_data": json.dumps(cluster_data) if cluster_data is not None else None,
    })


def comments_table(request):
    """Ajax用: コメントテーブル部分のみを返す"""
    # 表示件数をクエリパラメータから取得（デフォルト: 30件）
    limit_options = [10, 30, 50]
    limit = int(request.GET.get('limit', 30))
    if limit not in limit_options:
        limit = 30
    
    # ページ番号を取得（デフォルト: 1ページ目）
    page_number = request.GET.get('page', 1)
    
    # テーブル表示用には全件を取得してページネーション
    all_comments = YouTubeComment.objects.all().order_by('-created_at')
    
    # ページネーション
    paginator = Paginator(all_comments, limit)
    page_obj = paginator.get_page(page_number)
    comments = page_obj.object_list

    from django.template.loader import render_to_string
    html = render_to_string('comments_table.html', {
        'comments': comments,
        'page_obj': page_obj,
        'current_limit': limit,
        'limit_options': limit_options,
    }, request=request)
    
    return JsonResponse({'html': html})


def import_csv(request):
    """CSVファイルをインポート"""
    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = TextIOWrapper(request.FILES["csv_file"].file, encoding="utf-8")
        reader = csv.DictReader(csv_file)
        count = 0
        for row in reader:
            YouTubeComment.objects.create(
                video_id=row.get("video_id", ""),
                comment_id=row.get("comment_id", ""),
                comment_text=row.get("comment_text", ""),
                author=row.get("author", ""),
                like_count=int(row.get("like_count") or 0),
                reply_count=int(row.get("reply_count") or 0),
                reply_depth_potential=int(row.get("reply_depth_potential") or 0),
                engagement_score=float(row.get("engagement_score") or 0),
                created_at=row.get("created_at") or None,
                ai_reply=row.get("ai_reply") if row.get("ai_reply") and row.get("ai_reply") != "null" else None,
                embedding=row.get("embedding") if row.get("embedding") else None,
            )
            count += 1
        messages.success(request, f"{count} 件のコメントをインポートしました。")
        return redirect("index")
    
    messages.error(request, "CSVファイルを選択してください。")
    return redirect("index")


def import_json(request):
    """JSONファイルをインポート"""
    if request.method == "POST" and request.FILES.get("json_file"):
        json_file = request.FILES["json_file"]
        try:
            data = json.load(json_file)
            count = 0
            
            # JSONが配列の場合
            if isinstance(data, list):
                for item in data:
                    YouTubeComment.objects.create(
                        video_id=item.get("video_id", ""),
                        comment_id=item.get("comment_id", ""),
                        comment_text=item.get("comment_text", ""),
                        author=item.get("author", ""),
                        like_count=int(item.get("like_count") or 0),
                        reply_count=int(item.get("reply_count") or 0),
                        reply_depth_potential=int(item.get("reply_depth_potential") or 0),
                        engagement_score=float(item.get("engagement_score") or 0),
                        created_at=item.get("created_at") or None,
                        ai_reply=item.get("ai_reply") if item.get("ai_reply") and item.get("ai_reply") != "null" else None,
                        embedding=item.get("embedding") if item.get("embedding") else None,
                    )
                    count += 1
            # JSONがオブジェクトでcommentsキーがある場合
            elif isinstance(data, dict) and "comments" in data:
                for item in data["comments"]:
                    YouTubeComment.objects.create(
                        video_id=item.get("video_id", ""),
                        comment_id=item.get("comment_id", ""),
                        comment_text=item.get("comment_text", ""),
                        author=item.get("author", ""),
                        like_count=int(item.get("like_count") or 0),
                        reply_count=int(item.get("reply_count") or 0),
                        reply_depth_potential=int(item.get("reply_depth_potential") or 0),
                        engagement_score=float(item.get("engagement_score") or 0),
                        created_at=item.get("created_at") or None,
                        ai_reply=item.get("ai_reply") if item.get("ai_reply") and item.get("ai_reply") != "null" else None,
                        embedding=item.get("embedding") if item.get("embedding") else None,
                    )
                    count += 1
            
            messages.success(request, f"{count} 件のコメントをインポートしました。")
            return redirect("index")
        except json.JSONDecodeError:
            messages.error(request, "JSONファイルの形式が正しくありません。")
            return redirect("index")
    
    messages.error(request, "JSONファイルを選択してください。")
    return redirect("index")


def pricing(request):
    # 現在のユーザーのプラン情報を取得
    current_plan = None
    current_user_plan = None
    if request.user.is_authenticated:
        try:
            current_user_plan = UserPlan.objects.get(user=request.user, is_active=True)
            current_plan = current_user_plan.plan
        except UserPlan.DoesNotExist:
            pass
    
    # すべてのプランを取得
    plans = Plan.objects.all().order_by('price')
    
    # Stripe公開キーとProプランの価格IDをテンプレートに渡す
    from django.conf import settings
    stripe_public_key = getattr(settings, 'STRIPE_PUBLIC_KEY', '')
    stripe_pro_price_id = getattr(settings, 'STRIPE_PRO_PRICE_ID', '')
    
    return render(request, "pricing.html", {
        "current_plan": current_plan,
        "current_user_plan": current_user_plan,
        "plans": plans,
        "user": request.user,  # テンプレートでユーザーIDを使用するため
        "stripe_public_key": stripe_public_key,
        "stripe_pro_price_id": stripe_pro_price_id,
    })


def downgrade_to_free(request):
    """Proプランから無料プランへ変更"""
    if not request.user.is_authenticated:
        messages.error(request, "ログインが必要です。")
        return redirect('pricing')
    
    if request.method == "POST":
        try:
            # 現在のユーザープランを取得
            user_plan = UserPlan.objects.get(user=request.user, is_active=True)
            current_plan = user_plan.plan
            
            # 無料プランを取得
            free_plan = Plan.objects.get(name='free')
            
            # プランを無料プランに変更
            user_plan.plan = free_plan
            user_plan.is_active = True
            user_plan.save()
            
            # 完了メッセージ
            messages.success(
                request,
                "ご利用ありがとうございました。\n"
                f"{current_plan.display_name if current_plan else 'Proプラン'}のご契約は終了し、無料プランへ変更されました。\n"
                "引き続き、無料プランにてサービスをご利用いただけます。"
            )
            
            return redirect('pricing')
        except UserPlan.DoesNotExist:
            messages.error(request, "ユーザープランが見つかりません。")
            return redirect('pricing')
        except Plan.DoesNotExist:
            messages.error(request, "無料プランが見つかりません。")
            return redirect('pricing')
    
    return redirect('pricing')


# ============================================
# Stripe決済機能
# ============================================
# 必要なパッケージ: pip install stripe
# インストールコマンド: pip install stripe

def create_checkout_session(request, plan_id):
    """
    Stripe Checkoutセッションを作成して決済画面にリダイレクト
    
    必要な設定:
    - settings.STRIPE_SECRET_KEY: Stripeシークレットキー
    - settings.STRIPE_SUCCESS_URL: 決済成功後のリダイレクトURL
    - settings.STRIPE_CANCEL_URL: 決済キャンセル時のリダイレクトURL
    - Plan.stripe_price_id: Stripe価格ID
    """
    if not request.user.is_authenticated:
        from django.contrib import messages
        messages.error(request, "ログインが必要です。")
        return redirect('pricing')
    
    try:
        plan = Plan.objects.get(id=plan_id)
    except Plan.DoesNotExist:
        from django.contrib import messages
        messages.error(request, "プランが見つかりません。")
        return redirect('pricing')
    
    # 無料プランの場合は管理画面にリダイレクト
    if not plan.is_premium:
        from django.contrib import messages
        messages.info(request, "無料プランは管理画面から変更できます。")
        return redirect('admin:myapp_userplan_changelist')
    
    # Stripe価格IDを取得
    stripe_price_id = plan.stripe_price_id
    if not stripe_price_id:
        # settings.pyから取得（フォールバック）
        from django.conf import settings
        if plan.name == 'pro':
            stripe_price_id = getattr(settings, 'STRIPE_PRO_PRICE_ID', '')
    
    if not stripe_price_id:
        from django.contrib import messages
        messages.error(request, "このプランの決済設定が完了していません。管理画面から変更してください。")
        return redirect('admin:myapp_userplan_changelist')
    
    # Stripe Checkoutセッションを作成
    import stripe
    from django.conf import settings
    from django.contrib import messages
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Stripe APIキーの確認
    if not settings.STRIPE_SECRET_KEY:
        logger.error("Stripe APIキーが設定されていません")
        messages.error(request, "Stripe APIキーが設定されていません。")
        return redirect('pricing')
    
    # Stripe価格IDの確認
    if not stripe_price_id:
        logger.error(f"Stripe価格IDが取得できませんでした。plan_id: {plan_id}, plan.name: {plan.name}")
        messages.error(request, "このプランの決済設定が完了していません。")
        return redirect('pricing')
    
    logger.info(f"Stripe Checkoutセッション作成開始: plan_id={plan_id}, stripe_price_id={stripe_price_id}, user_id={request.user.id}")
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': stripe_price_id,
                'quantity': 1,
            }],
            mode='subscription',  # サブスクリプション（月額課金）
            success_url=settings.STRIPE_SUCCESS_URL + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=settings.STRIPE_CANCEL_URL,
            customer_email=request.user.email,
            metadata={
                'user_id': request.user.id,
                'plan_id': plan.id,
            },
        )
        
        logger.info(f"Stripe Checkoutセッション作成成功: session_id={checkout_session.id}, url={checkout_session.url}")
        
        # Checkout URLが正しく取得できたか確認
        if not checkout_session.url:
            logger.error("Stripe Checkout URLが取得できませんでした")
            messages.error(request, "Stripe Checkout URLの取得に失敗しました。")
            return redirect('pricing')
        
        # Stripe Checkoutページにリダイレクト
        return redirect(checkout_session.url)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe APIエラー: {str(e)}")
        messages.error(request, f"決済セッションの作成に失敗しました: {str(e)}")
        return redirect('pricing')
    except Exception as e:
        logger.error(f"予期しないエラー: {str(e)}", exc_info=True)
        messages.error(request, f"予期しないエラーが発生しました: {str(e)}")
        return redirect('pricing')


def checkout_success(request):
    """
    決済成功後のコールバック処理
    Stripe Checkoutからリダイレクトされた後に実行される
    """
    session_id = request.GET.get('session_id')
    
    if not session_id:
        from django.contrib import messages
        messages.error(request, "セッションIDが見つかりません。")
        return redirect('pricing')
    
    if not request.user.is_authenticated:
        from django.contrib import messages
        messages.error(request, "ログインが必要です。")
        return redirect('pricing')
    
    import stripe
    from django.conf import settings
    from django.contrib import messages
    from datetime import datetime, timedelta
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    try:
        # Checkoutセッションを取得
        session = stripe.checkout.Session.retrieve(session_id)
        
        # メタデータからユーザーIDとプランIDを取得
        user_id = session.metadata.get('user_id')
        plan_id = session.metadata.get('plan_id')
        
        # ユーザーが一致するか確認
        if int(user_id) != request.user.id:
            messages.error(request, "ユーザーが一致しません。")
            return redirect('pricing')
        
        # プランを取得
        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            messages.error(request, "プランが見つかりません。")
            return redirect('pricing')
        
        # ユーザープランを更新または作成
        user_plan, created = UserPlan.objects.get_or_create(
            user=request.user,
            defaults={'plan': plan, 'is_active': True}
        )
        
        if not created:
            user_plan.plan = plan
            user_plan.is_active = True
            # 有効期限を1ヶ月後に設定（サブスクリプションの場合）
            user_plan.expires_at = datetime.now() + timedelta(days=30)
            user_plan.save()
        
        messages.success(request, f"{plan.display_name}プランへの変更が完了しました。")
        return redirect('index')
        
    except stripe.error.StripeError as e:
        messages.error(request, f"決済情報の確認に失敗しました: {str(e)}")
        return redirect('pricing')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Stripe Webhookエンドポイント
    Stripeから決済完了などのイベントを受け取る
    
    必要な設定:
    - settings.STRIPE_WEBHOOK_SECRET: Webhook署名シークレット
    - StripeダッシュボードでWebhookエンドポイントを設定: https://yourdomain.com/stripe-webhook/
    - イベント: checkout.session.completed, customer.subscription.updated, customer.subscription.deleted
    """
    import stripe
    import json
    from django.conf import settings
    from django.http import HttpResponse
    from datetime import datetime, timedelta
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # イベントタイプに応じて処理
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # 決済完了時の処理
        user_id = session['metadata'].get('user_id')
        plan_id = session['metadata'].get('plan_id')
        
        # ユーザープランを更新
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            plan = Plan.objects.get(id=plan_id)
            
            user_plan, created = UserPlan.objects.get_or_create(
                user=user,
                defaults={'plan': plan, 'is_active': True}
            )
            
            if not created:
                user_plan.plan = plan
                user_plan.is_active = True
                user_plan.expires_at = datetime.now() + timedelta(days=30)
                user_plan.save()
        except (User.DoesNotExist, Plan.DoesNotExist):
            pass
        
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        # サブスクリプション更新時の処理
        # 必要に応じて実装
        
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        # サブスクリプション解約時の処理
        # ユーザーを無料プランに戻す
        try:
            customer_id = subscription.get('customer')
            # customer_idからuser_idを取得する処理が必要
            # 現時点では簡易実装
        except:
            pass
    
    return HttpResponse(status=200)


