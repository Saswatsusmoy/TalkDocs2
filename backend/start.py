#!/usr/bin/env python3
"""
Startup script for TalkDocs2 Backend
"""
import uvicorn
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Start the FastAPI server"""
    try:
        logger.info("Starting TalkDocs2 Backend Server...")
        
        # Check if running in development mode
        is_dev = os.getenv('ENVIRONMENT', 'development') == 'development'
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=is_dev,
            log_level="info" if is_dev else "warning"
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
