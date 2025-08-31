"""
PHCore FHIR Resource Loader
Loads and indexes FHIR resources from the resources directory.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class FhirResource:
    """Represents a FHIR resource with metadata."""
    id: str
    resource_type: str
    url: Optional[str]
    content: Dict[str, Any]
    source_file: str


class ResourceLoader:
    """Loads and manages FHIR resources from the resources directory."""
    
    def __init__(self, resources_dir: str = "resources", base_resources_dir: str = "fhir_base_resources"):
        self.resources_dir = Path(resources_dir)
        self.base_resources_dir = Path(base_resources_dir)
        self.resources: Dict[str, FhirResource] = {}
        self.by_type: Dict[str, List[FhirResource]] = {}
        self.by_url: Dict[str, FhirResource] = {}
        
    def load_all_resources(self) -> int:
        """Load all FHIR resources from both directories."""
        count = 0
        
        # Load PHCore resources
        if self.resources_dir.exists():
            count += self._load_from_directory(self.resources_dir)
            
        # Load base FHIR resources
        if self.base_resources_dir.exists():
            count += self._load_from_directory(self.base_resources_dir)
            
        self._print_resource_summary()
        return count
        
    def _load_from_directory(self, directory: Path) -> int:
        """Load resources from a specific directory."""
        count = 0
        for file_path in directory.glob("*.json"):
            try:
                resources = self._load_resource_file(file_path)
                count += len(resources)
            except Exception as e:
                print(f"⚠️ Error loading {file_path}: {e}")
        return count
        
    def _load_resource_file(self, file_path: Path) -> List[FhirResource]:
        """Load a single JSON file and return list of resources."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        resources = []
        
        # Handle Bundle resources (like valuesets.json)
        if data.get("resourceType") == "Bundle" and "entry" in data:
            for entry in data["entry"]:
                if "resource" in entry:
                    resource_data = entry["resource"]
                    resource = self._create_fhir_resource(resource_data, str(file_path))
                    if resource:
                        resources.append(resource)
                        self._index_resource(resource)
        else:
            # Handle single resources
            resource = self._create_fhir_resource(data, str(file_path))
            if resource:
                resources.append(resource)
                self._index_resource(resource)
                
        return resources
        
    def _create_fhir_resource(self, data: Dict[str, Any], source_file: str) -> Optional[FhirResource]:
        """Create a FhirResource from JSON data."""
        if "resourceType" not in data or "id" not in data:
            return None
            
        resource_type = data["resourceType"]
        resource_id = data["id"]
        url = data.get("url")
        
        return FhirResource(
            id=resource_id,
            resource_type=resource_type,
            url=url,
            content=data,
            source_file=source_file
        )
        
    def _index_resource(self, resource: FhirResource):
        """Index a resource for quick lookup."""
        # Index by ID
        self.resources[resource.id] = resource
        
        # Index by type
        if resource.resource_type not in self.by_type:
            self.by_type[resource.resource_type] = []
        self.by_type[resource.resource_type].append(resource)
        
        # Index by URL if available
        if resource.url:
            self.by_url[resource.url] = resource
            
    def get_resource(self, resource_type: str, resource_id: str) -> Optional[FhirResource]:
        """Get a resource by type and ID."""
        key = f"{resource_type}/{resource_id}"
        return self.resources.get(key)
        
    def get_resources_by_type(self, resource_type: str) -> List[FhirResource]:
        """Get all resources of a specific type."""
        return self.by_type.get(resource_type, [])
        
    def get_resource_by_url(self, url: str) -> Optional[FhirResource]:
        """Get a resource by its canonical URL."""
        return self.by_url.get(url)
        
    def get_all_resources(self) -> List[FhirResource]:
        """Get all loaded resources."""
        return list(self.resources.values())
        
    def _print_resource_summary(self) -> None:
        """Print a summary of loaded resources."""
        print("\nResource Summary:")
        for resource_type, resources in self.by_type.items():
            print(f"  {resource_type}: {len(resources)}")
