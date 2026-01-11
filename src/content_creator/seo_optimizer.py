"""
SEO Optimizer Module
Optimizes content for search engines
"""

from typing import Any, Dict, List


class SEOOptimizer:
    def __init__(self):
        self.max_title_length = 60
        self.max_description_length = 160

    def analyze_content(self, content: str, keywords: List[str]) -> Dict[str, Any]:
        """Analyze content for SEO"""
        return {
            "keyword_density": self._calculate_keyword_density(content, keywords),
            "readability": "good",
            "suggestions": self._generate_suggestions(content, keywords),
        }

    def _calculate_keyword_density(
        self, content: str, keywords: List[str]
    ) -> Dict[str, float]:
        """Calculate keyword density"""
        word_count = len(content.split())
        densities = {}
        for keyword in keywords:
            count = content.lower().count(keyword.lower())
            densities[keyword] = (count / word_count * 100) if word_count > 0 else 0
        return densities

    def _generate_suggestions(self, content: str, keywords: List[str]) -> List[str]:
        """Generate SEO suggestions"""
        suggestions = []
        if len(content) < 300:
            suggestions.append("Content is too short, aim for at least 300 words")
        return suggestions
