"""
ASGI entrypoint for Vercel deployment.

This module provides the ASGI application instance for serverless deployment
platforms like Vercel. It imports the FastHTML app from bridge.server and
exposes it as the ASGI application.
"""
from bridge.server import app

# Export the ASGI application for Vercel
# Vercel expects an 'app' variable at the module level
__all__ = ["app"]
