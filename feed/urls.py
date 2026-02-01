from django.urls import path
from .views import (
    PostListView,
    PostLikeView,
    CommentLikeView,
    LeaderboardView,
)

urlpatterns = [
    path("posts/", PostListView.as_view(), name="post-list"),
    path("posts/<int:post_id>/like/", PostLikeView.as_view(), name="post-like"),
    path("comments/<int:comment_id>/like/", CommentLikeView.as_view(), name="comment-like"),
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
]
