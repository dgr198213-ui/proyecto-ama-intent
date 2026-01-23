"""
ASGI configuration for Vercel deployment.

This module imports the FastHTML ASGI application from bridge.server
to allow Vercel to recognize and deploy it as an ASGI application.
"""

from bridge.server import app

# Expose the app for ASGI servers (Vercel, Uvicorn, etc.)
__all__ = ['app']
