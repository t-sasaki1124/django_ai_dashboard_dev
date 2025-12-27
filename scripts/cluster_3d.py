"""
3D Clustering Visualization Script for Comment Analysis
"""
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import plotly.graph_objects as go
import plotly.express as px
import argparse
import sys
from pathlib import Path


def load_csv(filepath):
    """Load CSV file with pandas."""
    return pd.read_csv(filepath)


def detect_text_column(df):
    """Detect or accept text column for comments."""
    possible_columns = ['comment_text', 'text', 'comment', 'content', 'message']
    for col in possible_columns:
        if col in df.columns:
            return col
    # If no standard column found, return first string column
    for col in df.columns:
        if df[col].dtype == 'object':
            return col
    raise ValueError("No suitable text column found in CSV")


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


def vectorize_comments(comments, max_features=1000):
    """Vectorize comments using TF-IDF."""
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        stop_words=None,  # Keep all words for Japanese/English
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.95
    )
    vectors = vectorizer.fit_transform(comments)
    return vectors, vectorizer


def reduce_to_3d(vectors):
    """Reduce vectors to 3 dimensions using PCA."""
    pca = PCA(n_components=3, random_state=42)
    reduced = pca.fit_transform(vectors.toarray())
    return reduced, pca


def cluster_comments(vectors_3d, n_clusters=10):
    """Cluster comments using KMeans."""
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(vectors_3d)
    return cluster_labels, kmeans


def create_3d_visualization(vectors_3d, cluster_labels, comments, output_path):
    """Create interactive 3D scatter plot using Plotly."""
    # Create color map for clusters
    n_clusters = len(np.unique(cluster_labels))
    colors = px.colors.qualitative.Set3[:n_clusters]
    
    fig = go.Figure()
    
    for cluster_id in range(n_clusters):
        mask = cluster_labels == cluster_id
        cluster_points = vectors_3d[mask]
        cluster_comments = [comments[i] for i in range(len(comments)) if mask[i]]
        
        fig.add_trace(go.Scatter3d(
            x=cluster_points[:, 0],
            y=cluster_points[:, 1],
            z=cluster_points[:, 2],
            mode='markers',
            marker=dict(
                size=5,
                color=colors[cluster_id % len(colors)],
                opacity=0.7
            ),
            name=f'Cluster {cluster_id}',
            text=cluster_comments,
            hovertemplate='<b>Cluster %{fullData.name}</b><br>' +
                         'X: %{x:.2f}<br>' +
                         'Y: %{y:.2f}<br>' +
                         'Z: %{z:.2f}<br>' +
                         '<extra>%{text}</extra>'
        ))
    
    fig.update_layout(
        title='3D Comment Clustering Visualization',
        scene=dict(
            xaxis_title='PC1',
            yaxis_title='PC2',
            zaxis_title='PC3'
        ),
        width=1200,
        height=800
    )
    
    fig.write_html(output_path)


def main():
    parser = argparse.ArgumentParser(description='3D Clustering Visualization of Comments')
    parser.add_argument('--input', '-i', type=str, default='comments.csv',
                       help='Input CSV file path (default: comments.csv)')
    parser.add_argument('--output', '-o', type=str, default='cluster_3d_visualization.html',
                       help='Output HTML file path (default: cluster_3d_visualization.html)')
    parser.add_argument('--clusters', '-c', type=int, default=10,
                       help='Number of clusters (default: 10)')
    parser.add_argument('--text-column', '-t', type=str, default=None,
                       help='Text column name (auto-detected if not specified)')
    
    args = parser.parse_args()
    
    # Load CSV
    print(f"Loading CSV from {args.input}...")
    df = load_csv(args.input)
    print(f"Loaded {len(df)} rows")
    
    # Detect text column
    text_column = args.text_column if args.text_column else detect_text_column(df)
    print(f"Using text column: {text_column}")
    
    # Extract and clean comments
    print("Cleaning text...")
    comments = df[text_column].apply(clean_text).tolist()
    comments = [c for c in comments if c]  # Remove empty comments
    print(f"Processed {len(comments)} non-empty comments")
    
    if len(comments) < args.clusters:
        print(f"Warning: Number of comments ({len(comments)}) is less than number of clusters ({args.clusters})")
        args.clusters = max(2, len(comments) // 2)
        print(f"Adjusting clusters to {args.clusters}")
    
    # Vectorize
    print("Vectorizing comments with TF-IDF...")
    vectors, vectorizer = vectorize_comments(comments)
    print(f"Vector shape: {vectors.shape}")
    
    # Reduce to 3D
    print("Reducing to 3 dimensions with PCA...")
    vectors_3d, pca = reduce_to_3d(vectors)
    print(f"Explained variance ratio: {pca.explained_variance_ratio_.sum():.3f}")
    
    # Cluster
    print(f"Clustering into {args.clusters} clusters...")
    cluster_labels, kmeans = cluster_comments(vectors_3d, n_clusters=args.clusters)
    print(f"Cluster distribution: {np.bincount(cluster_labels)}")
    
    # Visualize
    print(f"Creating visualization...")
    create_3d_visualization(vectors_3d, cluster_labels, comments, args.output)
    print(f"Visualization saved to {args.output}")


if __name__ == '__main__':
    main()

