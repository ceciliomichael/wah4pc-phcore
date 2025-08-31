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
import requests


class FhirValidationClient:
    """Client for PHCore FHIR validation server."""
    
    def __init__(self, base_url: str = "http://localhost:5072"):
        self.base_url = base_url.rstrip('/')
        
    def validate_resource(self, resource_data: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
        """Validate a FHIR resource against PHCore profiles."""
        try:
            if verbose:
                # Send verbose validation request
                payload = {
                    "resource": resource_data,
                    "verbose": True
                }
            else:
                # Send regular validation request
                payload = resource_data
                
            response = requests.post(
                f"{self.base_url}/ph-core/fhir/$validate",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "resourceType": "OperationOutcome",
                    "issue": [{
                        "severity": "error",
                        "code": "http-error",
                        "details": {"text": f"HTTP {response.status_code}: {response.text}"}
                    }]
                }
        except requests.exceptions.RequestException as e:
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
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("Usage: python client.py <command> [args...]")
        print("Commands:")
        print("  validate <file.json> [--verbose]  - Validate a FHIR resource")
        print("  profiles                          - List available profiles")
        print("  resource <type> <id>             - Get a specific resource")
        print("  test                             - Run validation tests")
        return
    
    client = FhirValidationClient()
    command = sys.argv[1]
    
    if command == "validate":
        if len(sys.argv) < 3:
            print("Usage: python client.py validate <file.json> [--verbose]")
            return
        
        file_path = sys.argv[2]
        verbose = "--verbose" in sys.argv
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                resource_data = json.load(f)
            
            print(f"🔍 Validating {file_path}{'(verbose mode)' if verbose else ''}...")
            result = client.validate_resource(resource_data, verbose=verbose)
            
            print(json.dumps(result, indent=2))
            
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {file_path}: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif command == "profiles":
        result = client.get_profiles()
        if 'profiles' in result:
            print("📋 Available PHCore Profiles:")
            for profile in result['profiles']:
                print(f"  - {profile}")
        else:
            print(json.dumps(result, indent=2))
    
    elif command == "resource":
        if len(sys.argv) < 4:
            print("Usage: python client.py resource <type> <id>")
            return
        
        resource_type = sys.argv[2]
        resource_id = sys.argv[3]
        
        result = client.get_resource(resource_type, resource_id)
        print(json.dumps(result, indent=2))
    
    elif command == "test":
        print("🧪 Running validation tests...")
        
        # Test valid patient
        try:
            with open('examples/valid/patient/patient_from_hospital_emr.json', 'r') as f:
                valid_patient = json.load(f)
            
            print("\n✅ Testing valid patient...")
            result = client.validate_resource(valid_patient)
            is_valid = not any(issue.get('severity') == 'error' for issue in result.get('issue', []))
            print(f"Result: {'✅ VALID' if is_valid else '❌ INVALID'}")
            
        except FileNotFoundError:
            print("❌ Valid patient example not found")
        
        # Test invalid patient
        try:
            with open('examples/invalid/patient/patient_missing_extension.json', 'r') as f:
                invalid_patient = json.load(f)
            
            print("\n❌ Testing invalid patient...")
            result = client.validate_resource(invalid_patient)
            is_valid = not any(issue.get('severity') == 'error' for issue in result.get('issue', []))
            print(f"Result: {'✅ VALID' if is_valid else '❌ INVALID (as expected)'}")
            
        except FileNotFoundError:
            print("❌ Invalid patient example not found")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: validate, profiles, resource, test")


if __name__ == "__main__":
    main()
