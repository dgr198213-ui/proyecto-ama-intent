"""
ASGI entrypoint for Vercel deployment.

This file exports the ASGI application instance that Vercel expects
to find in the root directory for ASGI application deployment.
"""
from bridge.server import app

# Export the ASGI application for Vercel
__all__ = ['app']
