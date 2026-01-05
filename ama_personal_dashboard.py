#!/usr/bin/env python3
"""
AMA-Intent Personal Dashboard
Main entry point for the personal development tools
"""

import sys
import uvicorn
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_dashboard.web_ui import app

def main():
    """Start the dashboard server"""
    print("🚀 Starting AMA-Intent Personal Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8000")
    print("🔧 Debug Assistant: http://localhost:8000/debug")
    print("✍️  Content Creator: http://localhost:8000/content")
    print("📁 Projects: http://localhost:8000/projects")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
