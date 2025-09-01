"""
PHCore FHIR Playground Routes
FastAPI routes for the interactive playground interface.
"""

import json
from typing import Dict, Any, Union
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from .app import PlaygroundApp


class ValidationRequest(BaseModel):
    """Request model for playground validation."""
    resource: Dict[str, Any]
    verbose: bool = False


def setup_playground_routes(app: FastAPI, playground_app: PlaygroundApp) -> None:
    """
    Set up all playground routes in the FastAPI application.
    
    Args:
        app: FastAPI application instance
        playground_app: PlaygroundApp instance
    """
    
    @app.get("/playground", response_class=HTMLResponse)
    async def playground_home(request: Request):
        """Playground home page with interactive interface."""
        return playground_app.templates.TemplateResponse("playground.html", {
            "request": request,
            "title": "PHCore FHIR Playground",
            "quick_examples": playground_app.get_quick_start_examples(),
            "documentation_links": playground_app.get_documentation_links(),
            "available_profiles": playground_app.get_available_profiles()
        })
        
    @app.get("/playground/docs", response_class=HTMLResponse) 
    async def playground_docs(request: Request):
        """Playground documentation page."""
        return playground_app.templates.TemplateResponse("docs.html", {
            "request": request,
            "title": "PHCore Playground Documentation",
            "documentation_links": playground_app.get_documentation_links(),
            "available_profiles": playground_app.get_available_profiles()
        })
        
    @app.get("/playground/examples", response_class=HTMLResponse)
    async def playground_examples(request: Request):
        """Playground examples browser."""
        return playground_app.templates.TemplateResponse("examples.html", {
            "request": request,
            "title": "PHCore FHIR Examples",
            "valid_examples": playground_app.examples["valid"],
            "invalid_examples": playground_app.examples["invalid"]
        })
        
    @app.get("/playground/validator", response_class=HTMLResponse)
    async def playground_validator(request: Request):
        """Playground FHIR validator interface."""
        return playground_app.templates.TemplateResponse("validator.html", {
            "request": request,
            "title": "PHCore FHIR Validator",
            "quick_examples": playground_app.get_quick_start_examples()
        })
        
    @app.get("/playground/ai-helper", response_class=HTMLResponse)
    async def playground_ai_helper(request: Request):
        """Playground AI Helper interface (under construction)."""
        return playground_app.templates.TemplateResponse("ai-helper.html", {
            "request": request,
            "title": "PHCore AI Helper - Under Construction"
        })
        
    @app.post("/playground/api/validate")
    async def playground_validate_api(request: ValidationRequest):
        """
        API endpoint for validating FHIR resources from the playground.
        
        Args:
            request: ValidationRequest with resource data and options
            
        Returns:
            JSON response with validation results
        """
        try:
            result = playground_app.validate_example_resource(
                request.resource, 
                verbose=request.verbose
            )
            return JSONResponse(content=result)
            
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": f"Validation failed: {str(e)}",
                    "issues": [{
                        "severity": "error",
                        "code": "exception",
                        "details": str(e),
                        "location": "root",
                        "severity_class": "error"
                    }]
                }
            )
            
    @app.get("/playground/api/examples/{validity}/{resource_type}")
    async def get_examples(validity: str, resource_type: str):
        """
        Get examples by validity and resource type.
        
        Args:
            validity: "valid" or "invalid"
            resource_type: FHIR resource type (e.g., "patient", "encounter")
            
        Returns:
            JSON list of examples
        """
        if validity not in ["valid", "invalid"]:
            raise HTTPException(status_code=400, detail="Validity must be 'valid' or 'invalid'")
            
        examples = playground_app.examples.get(validity, {}).get(resource_type, [])
        if not examples:
            raise HTTPException(
                status_code=404, 
                detail=f"No {validity} examples found for resource type: {resource_type}"
            )
            
        return JSONResponse(content=examples)
        
    @app.get("/playground/api/example/{validity}/{resource_type}/{filename}")
    async def get_specific_example(validity: str, resource_type: str, filename: str):
        """
        Get a specific example by validity, resource type, and filename.
        
        Args:
            validity: "valid" or "invalid"
            resource_type: FHIR resource type
            filename: Example filename
            
        Returns:
            JSON response with example data
        """
        if validity not in ["valid", "invalid"]:
            raise HTTPException(status_code=400, detail="Validity must be 'valid' or 'invalid'")
            
        examples = playground_app.examples.get(validity, {}).get(resource_type, [])
        
        for example in examples:
            if example["filename"] == filename:
                return JSONResponse(content=example)
                
        raise HTTPException(
            status_code=404, 
            detail=f"Example not found: {validity}/{resource_type}/{filename}"
        )
        
    @app.get("/playground/api/profiles")
    async def get_playground_profiles():
        """Get available PHCore profiles for the playground."""
        profiles = playground_app.get_available_profiles()
        return JSONResponse(content={"profiles": profiles})
        
    @app.get("/playground/api/profile/{profile_id}")
    async def get_playground_profile(profile_id: str):
        """
        Get specific profile information for the playground.
        
        Args:
            profile_id: StructureDefinition ID
            
        Returns:
            JSON response with profile details
        """
        profile = playground_app.resource_loader.get_resource("StructureDefinition", profile_id)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"Profile not found: {profile_id}"
            )
            
        return JSONResponse(content=profile.content)
        
    @app.post("/playground/api/validate-example")
    async def validate_example_from_form(
        example_data: str = Form(...),
        verbose: bool = Form(False)
    ):
        """
        Validate FHIR resource from form data (for HTML forms).
        
        Args:
            example_data: JSON string of FHIR resource
            verbose: Whether to perform verbose validation
            
        Returns:
            JSON response with validation results
        """
        try:
            # Parse JSON data
            resource_data = json.loads(example_data)
            
            # Validate the resource
            result = playground_app.validate_example_resource(resource_data, verbose=verbose)
            
            return JSONResponse(content=result)
            
        except json.JSONDecodeError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": f"Invalid JSON: {str(e)}",
                    "issues": [{
                        "severity": "error",
                        "code": "invalid",
                        "details": f"JSON parsing error: {str(e)}",
                        "location": "root",
                        "severity_class": "error"
                    }]
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": f"Validation failed: {str(e)}",
                    "issues": [{
                        "severity": "error",
                        "code": "exception",
                        "details": str(e),
                        "location": "root",
                        "severity_class": "error"
                    }]
                }
            )
