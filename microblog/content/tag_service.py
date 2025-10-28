"""
Tag service for managing blog post tags.

This module provides tag management functionality including tag extraction,
autocomplete suggestions, and tag-based filtering operations.
"""

import logging
from collections import Counter

from microblog.content.post_service import get_post_service

logger = logging.getLogger(__name__)


class TagService:
    """
    Service for managing blog post tags.

    Features:
    - Extract all tags from posts
    - Provide autocomplete suggestions
    - Tag usage statistics
    - Tag validation and normalization
    """

    def __init__(self):
        """Initialize the tag service."""
        self._post_service = get_post_service()
        logger.info("Tag service initialized")

    def get_all_tags(self, include_drafts: bool = True) -> list[str]:
        """
        Get all unique tags from posts, sorted by usage frequency.

        Args:
            include_drafts: Whether to include tags from draft posts

        Returns:
            List of unique tags sorted by frequency (most used first)
        """
        try:
            posts = self._post_service.list_posts(include_drafts=include_drafts)
            tag_counter = Counter()

            for post in posts:
                for tag in post.frontmatter.tags:
                    # Normalize tag (strip whitespace, lowercase for counting)
                    normalized_tag = tag.strip()
                    if normalized_tag:
                        tag_counter[normalized_tag] += 1

            # Return tags sorted by frequency (most used first)
            return [tag for tag, count in tag_counter.most_common()]

        except Exception as e:
            logger.error(f"Failed to get all tags: {e}")
            return []

    def get_tag_suggestions(self, query: str, limit: int = 10, include_drafts: bool = True) -> list[dict[str, any]]:
        """
        Get tag suggestions based on a query string.

        Args:
            query: Search query for tag autocomplete
            limit: Maximum number of suggestions to return
            include_drafts: Whether to include tags from draft posts

        Returns:
            List of tag suggestion dictionaries with 'tag', 'count', and 'exact_match' fields
        """
        try:
            if not query or not query.strip():
                return []

            query = query.strip().lower()
            posts = self._post_service.list_posts(include_drafts=include_drafts)
            tag_counter = Counter()

            # Collect all tags with their usage counts
            for post in posts:
                for tag in post.frontmatter.tags:
                    normalized_tag = tag.strip()
                    if normalized_tag:
                        tag_counter[normalized_tag] += 1

            # Filter and rank suggestions
            suggestions = []

            for tag, count in tag_counter.items():
                tag_lower = tag.lower()

                # Check for matches
                if query in tag_lower:
                    exact_match = tag_lower == query
                    starts_with = tag_lower.startswith(query)

                    # Score for ranking: exact match > starts with > contains
                    if exact_match:
                        score = 1000 + count  # Highest priority
                    elif starts_with:
                        score = 500 + count   # Second priority
                    else:
                        score = count         # Lowest priority

                    suggestions.append({
                        'tag': tag,
                        'count': count,
                        'exact_match': exact_match,
                        'score': score
                    })

            # Sort by score (descending) and take top results
            suggestions.sort(key=lambda x: x['score'], reverse=True)

            # Remove score from returned results and limit
            return [{k: v for k, v in s.items() if k != 'score'} for s in suggestions[:limit]]

        except Exception as e:
            logger.error(f"Failed to get tag suggestions for query '{query}': {e}")
            return []

    def get_tag_stats(self, include_drafts: bool = True) -> dict[str, any]:
        """
        Get tag usage statistics.

        Args:
            include_drafts: Whether to include tags from draft posts

        Returns:
            Dictionary with tag statistics
        """
        try:
            posts = self._post_service.list_posts(include_drafts=include_drafts)
            tag_counter = Counter()
            total_posts = len(posts)
            tagged_posts = 0

            for post in posts:
                if post.frontmatter.tags:
                    tagged_posts += 1
                    for tag in post.frontmatter.tags:
                        normalized_tag = tag.strip()
                        if normalized_tag:
                            tag_counter[normalized_tag] += 1

            unique_tags = len(tag_counter)
            total_tag_usages = sum(tag_counter.values())
            avg_tags_per_post = total_tag_usages / total_posts if total_posts > 0 else 0

            return {
                'total_posts': total_posts,
                'tagged_posts': tagged_posts,
                'untagged_posts': total_posts - tagged_posts,
                'unique_tags': unique_tags,
                'total_tag_usages': total_tag_usages,
                'avg_tags_per_post': round(avg_tags_per_post, 2),
                'most_used_tags': dict(tag_counter.most_common(10))
            }

        except Exception as e:
            logger.error(f"Failed to get tag statistics: {e}")
            return {
                'total_posts': 0,
                'tagged_posts': 0,
                'untagged_posts': 0,
                'unique_tags': 0,
                'total_tag_usages': 0,
                'avg_tags_per_post': 0,
                'most_used_tags': {}
            }

    def validate_tags(self, tags: list[str]) -> list[str]:
        """
        Validate and normalize a list of tags.

        Args:
            tags: List of tag strings to validate

        Returns:
            List of validated and normalized tags
        """
        if not tags:
            return []

        validated_tags = []
        seen_tags = set()

        for tag in tags:
            if not isinstance(tag, str):
                continue

            # Normalize tag
            normalized_tag = tag.strip()

            # Skip empty tags
            if not normalized_tag:
                continue

            # Skip overly long tags
            if len(normalized_tag) > 50:
                logger.warning(f"Tag too long, skipping: {normalized_tag[:20]}...")
                continue

            # Avoid duplicates (case-insensitive)
            tag_lower = normalized_tag.lower()
            if tag_lower in seen_tags:
                continue

            seen_tags.add(tag_lower)
            validated_tags.append(normalized_tag)

        return validated_tags

    def get_posts_by_tag(self, tag: str, include_drafts: bool = False) -> list:
        """
        Get posts that have a specific tag.

        Args:
            tag: Tag to filter by
            include_drafts: Whether to include draft posts

        Returns:
            List of PostContent objects with the specified tag
        """
        try:
            return self._post_service.list_posts(
                include_drafts=include_drafts,
                tag_filter=tag
            )
        except Exception as e:
            logger.error(f"Failed to get posts by tag '{tag}': {e}")
            return []

    def get_related_tags(self, tag: str, limit: int = 5, include_drafts: bool = True) -> list[dict[str, any]]:
        """
        Get tags that commonly appear together with the given tag.

        Args:
            tag: The tag to find related tags for
            limit: Maximum number of related tags to return
            include_drafts: Whether to include tags from draft posts

        Returns:
            List of related tag dictionaries with 'tag' and 'co_occurrence_count' fields
        """
        try:
            posts = self._post_service.list_posts(include_drafts=include_drafts)
            tag_lower = tag.lower()
            related_counter = Counter()

            # Find posts that contain the target tag
            for post in posts:
                post_tags = [t.strip() for t in post.frontmatter.tags]
                post_tags_lower = [t.lower() for t in post_tags]

                if tag_lower in post_tags_lower:
                    # Count co-occurrence of other tags
                    for other_tag in post_tags:
                        if other_tag.strip() and other_tag.lower() != tag_lower:
                            related_counter[other_tag.strip()] += 1

            # Return top related tags
            return [
                {'tag': related_tag, 'co_occurrence_count': count}
                for related_tag, count in related_counter.most_common(limit)
            ]

        except Exception as e:
            logger.error(f"Failed to get related tags for '{tag}': {e}")
            return []


# Global tag service instance
_tag_service: TagService | None = None


def get_tag_service() -> TagService:
    """
    Get the global tag service instance.

    Returns:
        TagService instance
    """
    global _tag_service
    if _tag_service is None:
        _tag_service = TagService()
    return _tag_service
