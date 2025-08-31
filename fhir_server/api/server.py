"""
PHCore FHIR Validation Server
FastAPI server providing FHIR REST endpoints and validation services.
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from fhir_server.core.resource_loader import ResourceLoader
from fhir_server.validation.validator import FhirValidator, ValidationResult


class ValidationRequest(BaseModel):
    """Request model for resource validation."""
    resource: Dict[str, Any]
    profile: Optional[str] = None


class FhirServer:
    """FastAPI-based FHIR server for PHCore resources."""
    
    def __init__(self):
        self.app = FastAPI(
            title="PHCore FHIR Validation Server",
            description="FHIR validation server for Philippine Core Implementation Guide",
            version="1.0.0"
        )
        
        # Initialize resource loader and validator
        self.resource_loader = ResourceLoader()
        count = self.resource_loader.load_all_resources()
        print(f"Loaded {count} FHIR resources")
        
        self.validator = FhirValidator(self.resource_loader)
        
        # Set up routes
        self._setup_routes()
        
    def _setup_routes(self) -> None:
        """Set up FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            """Server information."""
            return {
                "resourceType": "CapabilityStatement",
                "id": "phcore-validation-server",
                "status": "active",
                "date": "2025-01-27",
                "publisher": "PHCore Implementation Guide",
                "kind": "instance",
                "software": {
                    "name": "PHCore FHIR Validation Server",
                    "version": "1.0.0"
                },
                "implementation": {
                    "description": "PHCore FHIR Validation Server",
                    "url": "http://localhost:5072"
                },
                "fhirVersion": "4.0.1",
                "format": ["json"],
                "rest": [{
                    "mode": "server",
                    "resource": [
                        {
                            "type": resource_type,
                            "interaction": [
                                {"code": "read"},
                                {"code": "search-type"}
                            ]
                        }
                        for resource_type in self.resource_loader.resources_by_type.keys()
                    ]
                }]
            }
            
        @self.app.get("/ph-core/fhir/metadata")
        async def metadata():
            """FHIR metadata endpoint."""
            return await root()
            
        @self.app.post("/ph-core/fhir/$validate")
        async def validate_resource(request: ValidationRequest):
            """Validate a FHIR resource."""
            try:
                result = self.validator.validate_resource(
                    request.resource, 
                    request.profile
                )
                
                # Convert to FHIR OperationOutcome format
                outcome = self._create_operation_outcome(result)
                
                return JSONResponse(
                    content=outcome,
                    status_code=200 if result.is_valid else 400
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/ph-core/fhir/profiles")
        async def list_profiles():
            """List available StructureDefinition profiles."""
            profiles = []
            for url in self.validator.get_available_profiles():
                profile_info = self.validator.get_profile_info(url)
                if profile_info:
                    profiles.append(profile_info)
            return {"profiles": profiles}
            
        @self.app.get("/ph-core/fhir/{resource_type}")
        async def search_resources(resource_type: str):
            """Search resources by type."""
            resources = self.resource_loader.get_resources_by_type(resource_type)
            if not resources:
                raise HTTPException(status_code=404, detail=f"No resources found for type: {resource_type}")
                
            bundle = {
                "resourceType": "Bundle",
                "id": f"search-{resource_type}",
                "type": "searchset",
                "total": len(resources),
                "entry": [
                    {
                        "resource": resource.content,
                        "fullUrl": f"http://localhost:5072/ph-core/fhir/{resource_type}/{resource.resource_id}"
                    }
                    for resource in resources
                ]
            }
            
            return bundle
            
        @self.app.get("/ph-core/fhir/{resource_type}/{resource_id}")
        async def get_resource(resource_type: str, resource_id: str):
            """Get a specific resource by type and ID."""
            resource = self.resource_loader.get_resource(resource_type, resource_id)
            if not resource:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Resource not found: {resource_type}/{resource_id}"
                )
                
            return resource.content
            
        @self.app.get("/ph-core/fhir/ImplementationGuide/{ig_id}")
        async def get_implementation_guide(ig_id: str):
            """Get the Implementation Guide."""
            ig = self.resource_loader.get_resource("ImplementationGuide", ig_id)
            if not ig:
                raise HTTPException(
                    status_code=404, 
                    detail=f"ImplementationGuide not found: {ig_id}"
                )
            return ig.content
            
        @self.app.get("/ph-core/fhir/StructureDefinition/{profile_id}")
        async def get_structure_definition(profile_id: str):
            """Get a StructureDefinition profile."""
            sd = self.resource_loader.get_resource("StructureDefinition", profile_id)
            if not sd:
                raise HTTPException(
                    status_code=404, 
                    detail=f"StructureDefinition not found: {profile_id}"
                )
            return sd.content
            
        @self.app.get("/ph-core/fhir/ValueSet/{valueset_id}")
        async def get_value_set(valueset_id: str):
            """Get a ValueSet."""
            vs = self.resource_loader.get_resource("ValueSet", valueset_id)
            if not vs:
                raise HTTPException(
                    status_code=404, 
                    detail=f"ValueSet not found: {valueset_id}"
                )
            return vs.content
            
        @self.app.get("/ph-core/fhir/CodeSystem/{codesystem_id}")
        async def get_code_system(codesystem_id: str):
            """Get a CodeSystem."""
            cs = self.resource_loader.get_resource("CodeSystem", codesystem_id)
            if not cs:
                raise HTTPException(
                    status_code=404, 
                    detail=f"CodeSystem not found: {codesystem_id}"
                )
            return cs.content
            
    def _create_operation_outcome(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """Create FHIR OperationOutcome from validation result."""
        issues = []
        
        for issue in validation_result.issues:
            fhir_issue = {
                "severity": issue.severity,
                "code": issue.code,
                "details": {
                    "text": issue.details
                }
            }
            
            if issue.location:
                fhir_issue["location"] = [issue.location]
                
            issues.append(fhir_issue)
            
        # Add success message if no issues
        if not issues:
            issues.append({
                "severity": "information",
                "code": "informational",
                "details": {
                    "text": "Resource validation completed successfully"
                }
            })
            
        return {
            "resourceType": "OperationOutcome",
            "issue": issues
        }


def create_server(resources_dir: str = "resources") -> FastAPI:
    """Create and configure the FHIR server."""
    server = FhirServer()
    return server.app
