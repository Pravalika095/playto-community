from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework import status

from django.db import transaction, IntegrityError
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.contrib.auth.models import User

from .models import Post, Comment, PostLike, CommentLike
from .serializers import PostSerializer


# -------------------------
# POSTS LIST (N+1 OPTIMIZED)
# -------------------------
class PostListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        posts = (
            Post.objects
            .select_related("author")
            .prefetch_related(
                "likes",
                "comments__author",
                "comments__likes",
                "comments__replies__author",
                "comments__replies__likes",
            )
            .order_by("-created_at")
        )

        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)


# -------------------------
# POST LIKE
# -------------------------
class PostLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            with transaction.atomic():
                PostLike.objects.create(
                    user=request.user,
                    post=post
                )
        except IntegrityError:
            return Response(
                {"message": "You already liked this post"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "Post liked successfully"},
            status=status.HTTP_201_CREATED
        )


# -------------------------
# COMMENT LIKE
# -------------------------
class CommentLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return Response(
                {"error": "Comment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            with transaction.atomic():
                CommentLike.objects.create(
                    user=request.user,
                    comment=comment
                )
        except IntegrityError:
            return Response(
                {"message": "You already liked this comment"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "Comment liked successfully"},
            status=status.HTTP_201_CREATED
        )


# -------------------------
# LEADERBOARD (LAST 24 HOURS)
# -------------------------
from django.db.models import Q, Sum, Case, When, IntegerField


class LeaderboardView(APIView):

    def get(self, request):
        last_24h = timezone.now() - timedelta(hours=24)

        users = (
            User.objects
            .annotate(
                post_karma=Sum(
                    Case(
                        When(
                            posts__likes__created_at__gte=last_24h,
                            then=5
                        ),
                        default=0,
                        output_field=IntegerField()
                    )
                ),
                comment_karma=Sum(
                    Case(
                        When(
                            comments__likes__created_at__gte=last_24h,
                            then=1
                        ),
                        default=0,
                        output_field=IntegerField()
                    )
                )
            )
            .annotate(
                total_karma=(
                    (Sum(
                        Case(
                            When(
                                posts__likes__created_at__gte=last_24h,
                                then=5
                            ),
                            default=0,
                            output_field=IntegerField()
                        )
                    ) or 0)
                )
            )
        )

        users = (
            users
            .annotate(
                total_karma=(
                    (users.query.annotations['post_karma'] + users.query.annotations['comment_karma'])
                )
            )
            .order_by("-post_karma", "-comment_karma")[:5]
        )

        result = []

        for user in users:
            total = (user.post_karma or 0) + (user.comment_karma or 0)

            if total > 0:
                result.append({
                    "user_id": user.id,
                    "username": user.username,
                    "karma_last_24h": total
                })

        return Response(result)
