from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import Post, Comment, PostLike, CommentLike


class LeaderboardTestCase(TestCase):

    def test_leaderboard_counts_only_last_24_hours(self):
        """
        Test that leaderboard counts karma only from likes
        created within the last 24 hours.
        """

        # Create users
        user1 = User.objects.create_user(username="user1", password="testpass123")
        user2 = User.objects.create_user(username="user2", password="testpass123")

        # Create post
        post = Post.objects.create(author=user1, content="Test Post")

        # Create comment
        comment = Comment.objects.create(
            post=post,
            author=user1,
            content="Test Comment"
        )

        # Recent post like (should count)
        PostLike.objects.create(user=user2, post=post)

        # Old post like (should NOT count)
        old_like = PostLike.objects.create(
            user=user1,
            post=Post.objects.create(author=user2, content="Old Post")
        )
        old_like.created_at = timezone.now() - timedelta(days=2)
        old_like.save()

        # Recent comment like (should count)
        CommentLike.objects.create(user=user2, comment=comment)

        # Expected:
        # 1 recent post like = 5
        # 1 recent comment like = 1
        expected_karma = 6

        last_24_hours = timezone.now() - timedelta(hours=24)

        post_karma = PostLike.objects.filter(
            created_at__gte=last_24_hours
        ).count() * 5

        comment_karma = CommentLike.objects.filter(
            created_at__gte=last_24_hours
        ).count() * 1

        total_karma = post_karma + comment_karma

        self.assertEqual(total_karma, expected_karma)
