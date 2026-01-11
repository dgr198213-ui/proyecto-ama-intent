"""
Social Media Post Generator
Creates social media content
"""

from typing import Any, Dict, List


class SocialCraft:
    def __init__(self):
        self.platforms = ["twitter", "linkedin", "facebook", "instagram"]
        self.char_limits = {
            "twitter": 280,
            "linkedin": 3000,
            "facebook": 63206,
            "instagram": 2200,
        }

    def create_post(self, content: str, platform: str = "twitter") -> Dict[str, Any]:
        """Create social media post"""
        limit = self.char_limits.get(platform, 280)

        return {
            "platform": platform,
            "content": self._format_content(content, limit),
            "char_count": len(content),
            "char_limit": limit,
            "hashtags": self._suggest_hashtags(content),
        }

    def _format_content(self, content: str, limit: int) -> str:
        """Format content for platform"""
        if len(content) > limit:
            return content[: limit - 3] + "..."
        return content

    def _suggest_hashtags(self, content: str) -> List[str]:
        """Suggest relevant hashtags"""
        return ["#tech", "#coding", "#development"]
