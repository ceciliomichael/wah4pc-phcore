#!/usr/bin/env python3
"""
PHCore FHIR Validation Server
Main entry point to run the FHIR validation server.
"""

import uvicorn
from fhir_server.api.server import create_server


def main():
    """Start the FHIR validation server."""
    print("🚀 Starting PHCore FHIR Validation Server")
    print("📂 Loading resources from resources/ and fhir_base_resources/")
    print("🌐 Server will be available at: http://localhost:5072")
    print("📋 API Documentation: http://localhost:5072/docs")
    
    # Create the FastAPI app
    app = create_server()
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=5072)


if __name__ == "__main__":
    main()
