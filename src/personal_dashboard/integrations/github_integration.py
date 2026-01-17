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

    async def get_repo_activity_summary(self, owner: str, repo: str):
        """Obtiene un resumen de actividad reciente y genera un reporte de voz con MiniMax"""
        if not self.token:
            return "No hay token de GitHub configurado."

        async with aiohttp.ClientSession(headers=self.headers) as session:
            # Obtener commits recientes
            async with session.get(
                f"{self.base_url}/repos/{owner}/{repo}/commits?per_page=5"
            ) as resp:
                commits = await resp.json()

            if not commits or not isinstance(commits, list):
                return "No se encontró actividad reciente."

            summary_text = f"Resumen de actividad para {repo}: "
            for commit in commits:
                msg = commit.get("commit", {}).get("message", "Sin mensaje")
                author = (
                    commit.get("commit", {})
                    .get("author", {})
                    .get("name", "Desconocido")
                )
                summary_text += f"Commit de {author}: {msg}. "

            # Integración con MiniMax para reporte de voz
            from minimax_integration import AudioService

            audio = AudioService()
            audio_path = audio.text_to_speech(
                text=f"Hola, aquí tienes la actividad reciente de tu repositorio {repo}. {summary_text}",
                emotion="neutral",
            )

            return {
                "text_summary": summary_text,
                "audio_report": audio_path,
                "latest_commits": commits,
            }
