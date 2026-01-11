"""
Integración con GitHub API para AMA-Intent Personal Dashboard
Autor: Manus IA
Fecha: Enero 2026
"""

import asyncio
import base64
import hashlib
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
import requests
from requests.auth import HTTPBasicAuth

# ==================== MODELOS ====================


class GitHubEventType(Enum):
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    RELEASE = "release"


class GitHubConnector:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = (
            {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
            }
            if self.token
            else {}
        )

    async def get_user_repos(self):
        if not self.token:
            return []
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"{self.base_url}/user/repos") as resp:
                return await resp.json()
