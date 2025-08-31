#!/usr/bin/env python3
"""
PHCore FHIR Validation Client
Simple CLI client to test the FHIR validation server.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import urllib.request
import urllib.parse
import urllib.error


class FhirValidationClient:
    """Client for PHCore FHIR validation server."""
    
    def __init__(self, base_url: str = "http://localhost:5072"):
        self.base_url = base_url.rstrip('/')
        
    def validate_resource(self, resource_data: Dict[str, Any], profile_url: Optional[str] = None) -> Dict[str, Any]:
        """Validate a FHIR resource."""
        validation_request = {
            "resource": resource_data,
            "profile": profile_url
        }
        
        url = f"{self.base_url}/ph-core/fhir/$validate"
        
        try:
            data = json.dumps(validation_request).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
                
        except urllib.error.HTTPError as e:
            error_data = json.loads(e.read().decode('utf-8'))
            return error_data
        except Exception as e:
            return {
                "resourceType": "OperationOutcome",
                "issue": [{
                    "severity": "error",
                    "code": "exception",
                    "details": {"text": str(e)}
                }]
            }
            
    def get_profiles(self) -> Dict[str, Any]:
        """Get available profiles."""
        url = f"{self.base_url}/ph-core/fhir/profiles"
        
        try:
            with urllib.request.urlopen(url) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {"error": str(e)}
            
    def get_resource(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """Get a specific resource."""
        url = f"{self.base_url}/ph-core/fhir/{resource_type}/{resource_id}"
        
        try:
            with urllib.request.urlopen(url) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {"error": str(e)}


def main():
    """Main CLI function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python client.py validate <resource_file> [profile_url]")
        print("  python client.py profiles")
        print("  python client.py resource <type> <id>")
        print("  python client.py test")
        return
        
    client = FhirValidationClient()
    command = sys.argv[1]
    
    if command == "validate":
        if len(sys.argv) < 3:
            print("Error: Resource file required")
            return
            
        resource_file = sys.argv[2]
        profile_url = sys.argv[3] if len(sys.argv) > 3 else None
        
        try:
            with open(resource_file, 'r') as f:
                resource_data = json.load(f)
                
            result = client.validate_resource(resource_data, profile_url)
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"Error: {e}")
            
    elif command == "profiles":
        result = client.get_profiles()
        print(json.dumps(result, indent=2))
        
    elif command == "resource":
        if len(sys.argv) < 4:
            print("Error: Resource type and ID required")
            return
            
        resource_type = sys.argv[2]
        resource_id = sys.argv[3]
        
        result = client.get_resource(resource_type, resource_id)
        print(json.dumps(result, indent=2))
        
    elif command == "test":
        # Test with example patient
        print("🧪 Testing validation with example patient...")
        
        try:
            result = client.get_resource("Patient", "example-patient")
            if "error" not in result:
                validation_result = client.validate_resource(result)
                print("✅ Validation completed!")
                print(json.dumps(validation_result, indent=2))
            else:
                print(f"❌ Error getting example patient: {result['error']}")
        except Exception as e:
            print(f"❌ Test failed: {e}")
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
