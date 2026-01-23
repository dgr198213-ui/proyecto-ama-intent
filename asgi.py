"""
ASGI entry point for Vercel deployment.
This file exposes the FastHTML ASGI application for deployment on Vercel.
"""

from bridge.server import app

# Export the app for ASGI servers (like Vercel)
__all__ = ["app"]
