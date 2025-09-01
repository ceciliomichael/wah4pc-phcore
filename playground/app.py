"""
PHCore FHIR Playground Application
Main application class for the interactive testing environment.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from fhir_server.core.resource_loader import ResourceLoader
from fhir_server.validation.validator import FhirValidator


class PlaygroundApp:
    """
    Interactive playground application for PHCore FHIR testing.
    Provides a web-based interface for validation, documentation, and examples.
    """
    
    def __init__(self, resource_loader: ResourceLoader, validator: FhirValidator):
        """
        Initialize the playground application.
        
        Args:
            resource_loader: ResourceLoader instance for FHIR resources
            validator: FhirValidator instance for validation operations
        """
        self.resource_loader = resource_loader
        self.validator = validator
        
        # Initialize templates
        self.templates = self._setup_templates()
        
        # Load example resources
        self.examples = self._load_examples()
        
    def _setup_templates(self) -> Jinja2Templates:
        """Set up Jinja2 template environment."""
        templates_dir = Path(__file__).parent / "templates"
        templates_dir.mkdir(exist_ok=True)
        return Jinja2Templates(directory=str(templates_dir))
        
    def _load_examples(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Load example FHIR resources organized by validity and type.
        
        Returns:
            Dictionary with structure: {validity: {resource_type: [examples]}}
        """
        examples = {"valid": {}, "invalid": {}}
        examples_dir = Path("examples")
        
        if examples_dir.exists():
            for validity in ["valid", "invalid"]:
                validity_dir = examples_dir / validity
                if validity_dir.exists():
                    for resource_type_dir in validity_dir.iterdir():
                        if resource_type_dir.is_dir():
                            resource_type = resource_type_dir.name
                            examples[validity][resource_type] = []
                            
                            for example_file in resource_type_dir.glob("*.json"):
                                try:
                                    with open(example_file, 'r', encoding='utf-8') as f:
                                        example_data = json.load(f)
                                        examples[validity][resource_type].append({
                                            "filename": example_file.name,
                                            "filepath": str(example_file),
                                            "data": example_data,
                                            "description": self._get_example_description(example_data)
                                        })
                                except Exception as e:
                                    print(f"Warning: Could not load example {example_file}: {e}")
                                    
        return examples
        
    def _get_example_description(self, resource_data: Dict[str, Any]) -> str:
        """Generate a description for an example resource."""
        # Guard: ensure resource_data is a dict
        if not isinstance(resource_data, dict):
            try:
                # Attempt to parse if it's a JSON string
                if isinstance(resource_data, str):
                    parsed = json.loads(resource_data)
                    if isinstance(parsed, dict):
                        resource_data = parsed
                    else:
                        return "Unknown resource"
                else:
                    return "Unknown resource"
            except Exception:
                return "Unknown resource"
        
        resource_type = resource_data.get("resourceType", "Unknown")
        resource_id = resource_data.get("id", "no-id")
        
        if resource_type == "Patient":
            name = self._extract_patient_name(resource_data)
            return f"Patient: {name} (ID: {resource_id})"
        elif resource_type == "Encounter":
            status = resource_data.get("status", "unknown")
            return f"Encounter: {status} status (ID: {resource_id})"
        elif resource_type == "Observation":
            code_field = resource_data.get("code", {})
            if isinstance(code_field, dict):
                code = code_field.get("text", "Unknown observation")
            else:
                code = "Invalid code structure"
            return f"Observation: {code} (ID: {resource_id})"
        elif resource_type == "Medication":
            code_field = resource_data.get("code", {})
            if isinstance(code_field, dict):
                code = code_field.get("text", "Unknown medication")
            else:
                code = "Invalid code structure"
            return f"Medication: {code} (ID: {resource_id})"
        else:
            return f"{resource_type} (ID: {resource_id})"
            
    def _extract_patient_name(self, patient_data: Dict[str, Any]) -> str:
        """Extract patient name from Patient resource."""
        names = patient_data.get("name", [])
        if names and isinstance(names, list) and len(names) > 0:
            name = names[0]
            given = name.get("given", [])
            family = name.get("family", "")
            
            if given and family:
                return f"{' '.join(given)} {family}"
            elif family:
                return family
            elif given:
                return ' '.join(given)
                
        return "Unknown Patient"
        
    def get_available_profiles(self) -> List[Dict[str, Any]]:
        """Get list of available PHCore profiles."""
        profiles = []
        for url in self.validator.get_available_profiles():
            profile_info = self.validator.get_profile_info(url)
            if profile_info and "ph-core" in url:
                profiles.append(profile_info)
        return profiles
        
    def get_documentation_links(self) -> List[Dict[str, str]]:
        """Get documentation links for the playground."""
        return [
            {
                "title": "PHCore Implementation Guide",
                "description": "Official Philippine Core Implementation Guide",
                "url": "/ph-core/fhir/ImplementationGuide/localhost.fhir.ph.core"
            },
            {
                "title": "Available Profiles",
                "description": "List of all PHCore StructureDefinition profiles",
                "url": "/ph-core/fhir/profiles"
            },
            {
                "title": "Server Metadata",
                "description": "FHIR CapabilityStatement and server information",
                "url": "/ph-core/fhir/metadata"
            },
            {
                "title": "API Documentation",
                "description": "Interactive API documentation (Swagger UI)",
                "url": "/docs"
            }
        ]
        
    def get_quick_start_examples(self) -> List[Dict[str, Any]]:
        """Get quick start examples for common use cases."""
        quick_examples = []
        
        # Get one valid example for each resource type
        for resource_type, examples in self.examples["valid"].items():
            if examples:
                example = examples[0]  # First example
                quick_examples.append({
                    "resource_type": resource_type.title(),
                    "title": f"Valid {resource_type.title()} Example",
                    "description": example["description"],
                    "filename": example["filename"],
                    "data": example["data"]
                })
                
        return quick_examples[:4]  # Limit to 4 for UI
        
    def validate_example_resource(self, resource_data: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
        """
        Validate an example resource and return formatted result.
        
        Args:
            resource_data: FHIR resource to validate
            verbose: Whether to perform verbose validation
            
        Returns:
            Validation result with formatted issues
        """
        try:
            result = self.validator.validate_resource(resource_data, verbose=verbose)
            
            # Format issues for UI display
            formatted_issues = []
            for issue in result.issues:
                formatted_issues.append({
                    "severity": issue.severity,
                    "code": issue.code,
                    "details": issue.details,
                    "location": issue.location or "root",
                    "severity_class": self._get_severity_class(issue.severity)
                })
                
            return {
                "success": len(result.issues) == 0,
                "issues": formatted_issues,
                "total_issues": len(result.issues),
                "error_count": len([i for i in result.issues if i.severity == "error"]),
                "warning_count": len([i for i in result.issues if i.severity == "warning"])
            }
            
        except Exception as e:
            return {
                "success": False,
                "issues": [{
                    "severity": "error",
                    "code": "exception",
                    "details": f"Validation error: {str(e)}",
                    "location": "root",
                    "severity_class": "error"
                }],
                "total_issues": 1,
                "error_count": 1,
                "warning_count": 0
            }
            
    def _get_severity_class(self, severity: str) -> str:
        """Get CSS class for severity level."""
        severity_map = {
            "error": "error",
            "warning": "warning", 
            "information": "info",
            "fatal": "error"
        }
        return severity_map.get(severity, "info")
