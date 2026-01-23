"""
ASGI entrypoint for Vercel deployment.

This file exports the ASGI application instance that Vercel expects
to find in the root directory for ASGI application deployment.

The import from bridge.server initializes the database and creates
the LocalBrain instance as side effects, which is required for the
application to function properly.

Note: On Vercel (serverless), the database will be stored in /tmp
which is ephemeral. For persistent storage, consider using an external
database service.
"""
from bridge.server import app

# Export the ASGI application for Vercel
# The app variable is now available at module level for Vercel to discover
__all__ = ['app']
