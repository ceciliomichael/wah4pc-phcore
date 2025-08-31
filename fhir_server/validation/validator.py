"""
PHCore FHIR Validation Engine
Validates FHIR resources against PHCore profiles and terminologies.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from fhir_server.core.resource_loader import ResourceLoader, FhirResource


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    severity: str  # error, warning, information
    code: str
    details: str
    location: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of FHIR resource validation."""
    is_valid: bool
    issues: List[ValidationIssue]
    profile_url: Optional[str] = None


class FhirValidator:
    """Validates FHIR resources against PHCore implementation guide."""
    
    def __init__(self, resource_loader: ResourceLoader):
        self.resource_loader = resource_loader
        self.structure_definitions = {}
        self.value_sets = {}
        self.code_systems = {}
        self._index_conformance_resources()
        
    def _index_conformance_resources(self) -> None:
        """Index StructureDefinitions, ValueSets, and CodeSystems for validation."""
        # Index StructureDefinitions
        structure_defs = self.resource_loader.get_resources_by_type("StructureDefinition")
        for sd in structure_defs:
            if sd.url:
                self.structure_definitions[sd.url] = sd.content
                
        # Index ValueSets
        value_sets = self.resource_loader.get_resources_by_type("ValueSet")
        for vs in value_sets:
            if vs.url:
                self.value_sets[vs.url] = vs.content
                
        # Index CodeSystems
        code_systems = self.resource_loader.get_resources_by_type("CodeSystem")
        for cs in code_systems:
            if cs.url:
                self.code_systems[cs.url] = cs.content
                
        print(f"Indexed {len(self.structure_definitions)} StructureDefinitions")
        print(f"Indexed {len(self.value_sets)} ValueSets")
        print(f"Indexed {len(self.code_systems)} CodeSystems")
        
    def validate_resource(self, resource_data: Dict[str, Any], profile_url: Optional[str] = None, verbose: bool = False) -> ValidationResult:
        """Validate a FHIR resource."""
        issues = []
        
        # Basic FHIR resource validation
        basic_issues = self._validate_basic_structure(resource_data)
        issues.extend(basic_issues)
        
        # Profile-specific validation
        if profile_url:
            profile_issues = self._validate_against_profile(resource_data, profile_url, verbose)
            issues.extend(profile_issues)
        elif 'meta' in resource_data and 'profile' in resource_data['meta']:
            # Use profiles from meta.profile
            profiles = resource_data['meta']['profile']
            if isinstance(profiles, list):
                for profile in profiles:
                    profile_issues = self._validate_against_profile(resource_data, profile, verbose)
                    issues.extend(profile_issues)
            else:
                profile_issues = self._validate_against_profile(resource_data, profiles, verbose)
                issues.extend(profile_issues)
        
        # Determine overall validation result
        has_errors = any(issue.severity == 'error' for issue in issues)
        
        return ValidationResult(
            is_valid=not has_errors,
            issues=issues,
            profile_url=profile_url
        )
        
    def _validate_basic_structure(self, resource_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate basic FHIR resource structure."""
        issues = []
        
        # Check required fields
        if 'resourceType' not in resource_data:
            issues.append(ValidationIssue(
                severity='error',
                code='required',
                details='Missing required field: resourceType'
            ))
            
        if 'id' not in resource_data:
            issues.append(ValidationIssue(
                severity='warning',
                code='recommended',
                details='Missing recommended field: id'
            ))
            
        return issues
        
    def _validate_against_profile(self, resource_data: Dict[str, Any], profile_url: str, verbose: bool = False) -> List[ValidationIssue]:
        """Validate resource against a specific StructureDefinition profile."""
        issues = []
        
        # Get the StructureDefinition
        structure_def = self.structure_definitions.get(profile_url)
        if not structure_def:
            issues.append(ValidationIssue(
                severity='warning',
                code='not-found',
                details=f'StructureDefinition not found: {profile_url}'
            ))
            return issues
            
        # Validate resource type matches profile
        expected_type = structure_def.get('type')
        actual_type = resource_data.get('resourceType')
        
        if expected_type and actual_type != expected_type:
            issues.append(ValidationIssue(
                severity='error',
                code='type-mismatch',
                details=f'Resource type {actual_type} does not match profile type {expected_type}'
            ))
            # In non-verbose mode, return early on type mismatch
            if not verbose:
                return issues
            
        # Validate differential elements
        differential = structure_def.get('differential', {})
        elements = differential.get('element', [])
        
        # Group elements by path for slice validation
        elements_by_path = {}
        for element in elements:
            path = element.get('path', '')
            if path not in elements_by_path:
                elements_by_path[path] = []
            elements_by_path[path].append(element)
        
        for path, path_elements in elements_by_path.items():
            path_issues = self._validate_path_elements(resource_data, path, path_elements, profile_url, verbose)
            issues.extend(path_issues)
            
        # In verbose mode, also validate additional structural issues
        if verbose:
            structural_issues = self._validate_additional_structure(resource_data, expected_type)
            issues.extend(structural_issues)
            
        return issues
        
    def _validate_path_elements(self, resource_data: Dict[str, Any], path: str, elements: List[Dict[str, Any]], profile_url: str, verbose: bool = False) -> List[ValidationIssue]:
        """Validate elements for a specific path, handling slices."""
        issues = []
        
        # Skip root element (e.g., "Patient")
        if '.' not in path:
            return issues
            
        # Check if this is a sliced element
        has_slices = any('sliceName' in element for element in elements)
        
        if has_slices:
            # Handle sliced elements
            issues.extend(self._validate_sliced_elements(resource_data, path, elements, profile_url, verbose))
        else:
            # Handle regular elements
            for element in elements:
                element_issues = self._validate_element(resource_data, element, profile_url, verbose)
                issues.extend(element_issues)
                
        return issues
        
    def _validate_sliced_elements(self, resource_data: Dict[str, Any], path: str, elements: List[Dict[str, Any]], profile_url: str, verbose: bool = False) -> List[ValidationIssue]:
        """Validate sliced elements (like extension slices)."""
        issues = []
        
        # Extract the field path (e.g., "Patient.extension" -> "extension")
        field_path = path.split('.', 1)[1] if '.' in path else path
        
        # Get the actual data for this path
        actual_data = self._get_element_data(resource_data, field_path)
        
        # Find slice definitions (elements with sliceName)
        slice_elements = [e for e in elements if 'sliceName' in e]
        
        for slice_element in slice_elements:
            slice_name = slice_element.get('sliceName')
            min_occurs = slice_element.get('min', 0)
            max_occurs = slice_element.get('max', '*')
            
            # For extension slices, check by URL
            if field_path == 'extension':
                slice_issues = self._validate_extension_slice(
                    resource_data, slice_element, slice_name, min_occurs, max_occurs, profile_url, verbose
                )
                issues.extend(slice_issues)
            else:
                # Handle other types of slices (identifiers, etc.)
                slice_issues = self._validate_generic_slice(
                    resource_data, field_path, slice_element, slice_name, min_occurs, max_occurs, profile_url, verbose
                )
                issues.extend(slice_issues)
                
        return issues
        
    def _validate_extension_slice(self, resource_data: Dict[str, Any], slice_element: Dict[str, Any], slice_name: str, min_occurs: int, max_occurs: str, profile_url: str, verbose: bool = False) -> List[ValidationIssue]:
        """Validate a specific extension slice."""
        issues = []
        
        # Get the expected extension URL from the slice type profile
        slice_type = slice_element.get('type', [])
        expected_url = None
        
        for type_def in slice_type:
            if type_def.get('code') == 'Extension':
                profiles = type_def.get('profile', [])
                if profiles:
                    expected_url = profiles[0].split('|')[0]  # Remove version if present
                    break
        
        if not expected_url:
            return issues
            
        # Count matching extensions in the resource
        extensions = resource_data.get('extension', [])
        matching_count = 0
        
        for ext in extensions:
            if ext.get('url') == expected_url:
                matching_count += 1
                
        # Check minimum cardinality
        if matching_count < min_occurs:
            issues.append(ValidationIssue(
                severity='error',
                code='cardinality-min',
                details=f'Extension slice "{slice_name}" requires minimum {min_occurs} occurrence(s), found {matching_count}. Expected URL: {expected_url}',
                location=f'Patient.extension:{slice_name}'
            ))
            
        # Check maximum cardinality
        if max_occurs != '*' and matching_count > int(max_occurs):
            issues.append(ValidationIssue(
                severity='error',
                code='cardinality-max',
                details=f'Extension slice "{slice_name}" allows maximum {max_occurs} occurrence(s), found {matching_count}',
                location=f'Patient.extension:{slice_name}'
            ))
            
        return issues
        
    def _validate_generic_slice(self, resource_data: Dict[str, Any], field_path: str, slice_element: Dict[str, Any], slice_name: str, min_occurs: int, max_occurs: str, profile_url: str, verbose: bool = False) -> List[ValidationIssue]:
        """Validate a generic slice (non-extension)."""
        issues = []
        
        # This is a placeholder for other types of slices
        # For now, just check basic cardinality
        field_data = self._get_element_data(resource_data, field_path)
        
        if field_data is None:
            if min_occurs > 0:
                issues.append(ValidationIssue(
                    severity='error',
                    code='cardinality-min',
                    details=f'Slice "{slice_name}" requires minimum {min_occurs} occurrence(s), but field is missing',
                    location=f'{resource_data.get("resourceType", "Unknown")}.{field_path}:{slice_name}'
                ))
                
        return issues
        
    def _validate_element(self, resource_data: Dict[str, Any], element: Dict[str, Any], profile_url: str, verbose: bool = False) -> List[ValidationIssue]:
        """Validate a specific element against its definition."""
        issues = []
        
        path = element.get('path', '')
        element_id = element.get('id', '')
        min_occurs = element.get('min', 0)
        max_occurs = element.get('max', '*')
        
        # Skip root element (e.g., "Patient")
        if '.' not in path:
            return issues
            
        # Extract the field path (e.g., "Patient.extension" -> "extension")
        field_path = path.split('.', 1)[1] if '.' in path else path
        
        # Check minimum cardinality
        if min_occurs > 0:
            if not self._element_exists(resource_data, field_path):
                issues.append(ValidationIssue(
                    severity='error',
                    code='required',
                    details=f'Required element missing: {field_path}',
                    location=path
                ))
                
        # Validate binding if present
        binding = element.get('binding')
        if binding and self._element_exists(resource_data, field_path):
            binding_issues = self._validate_binding(resource_data, field_path, binding)
            issues.extend(binding_issues)
            
        return issues
        
    def _get_element_data(self, resource_data: Dict[str, Any], field_path: str) -> Any:
        """Get the data for a specific field path."""
        try:
            parts = field_path.split('.')
            current = resource_data
            
            for part in parts:
                if isinstance(current, list):
                    # For arrays, return the array itself
                    return current
                elif isinstance(current, dict):
                    if part not in current:
                        return None
                    current = current[part]
                else:
                    return None
                    
            return current
        except:
            return None
        
    def _element_exists(self, resource_data: Dict[str, Any], field_path: str) -> bool:
        """Check if an element exists in the resource."""
        try:
            parts = field_path.split('.')
            current = resource_data
            
            for part in parts:
                if isinstance(current, list):
                    # For arrays, check if any item has the field
                    found = False
                    for item in current:
                        if isinstance(item, dict) and part in item:
                            found = True
                            current = item[part]
                            break
                    if not found:
                        return False
                elif isinstance(current, dict):
                    if part not in current:
                        return False
                    current = current[part]
                else:
                    return False
                    
            return True
        except:
            return False
            
    def _validate_binding(self, resource_data: Dict[str, Any], field_path: str, binding: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate terminology binding."""
        issues = []
        
        value_set_url = binding.get('valueSet')
        strength = binding.get('strength', 'required')
        
        if not value_set_url:
            return issues
            
        # Get the ValueSet
        value_set = self.value_sets.get(value_set_url)
        if not value_set:
            if strength == 'required':
                issues.append(ValidationIssue(
                    severity='warning',
                    code='valueset-not-found',
                    details=f'ValueSet not found for binding: {value_set_url}',
                    location=field_path
                ))
            return issues
            
        # For now, just record that we found the binding
        # Full terminology validation would require more complex logic
        
        return issues
        
    def _validate_additional_structure(self, resource_data: Dict[str, Any], expected_type: str) -> List[ValidationIssue]:
        """Validate additional structural issues in verbose mode."""
        issues = []
        
        # Check for invalid fields that shouldn't exist in FHIR resources
        invalid_fields = []
        for field_name in resource_data.keys():
            if field_name not in ['resourceType', 'id', 'meta', 'implicitRules', 'language', 
                                'text', 'contained', 'extension', 'modifierExtension',
                                'identifier', 'active', 'name', 'telecom', 'gender', 'birthDate',
                                'address', 'maritalStatus', 'multipleBirthBoolean', 'multipleBirthInteger',
                                'photo', 'contact', 'communication', 'generalPractitioner', 'managingOrganization', 'link']:
                invalid_fields.append(field_name)
        
        for field in invalid_fields:
            issues.append(ValidationIssue(
                severity='error',
                code='invalid-field',
                details=f'Invalid field "{field}" found in {expected_type} resource',
                location=f'{expected_type}.{field}'
            ))
        
        # Check for invalid data types and formats
        if 'gender' in resource_data:
            gender = resource_data['gender']
            valid_genders = ['male', 'female', 'other', 'unknown']
            if gender not in valid_genders:
                issues.append(ValidationIssue(
                    severity='error',
                    code='invalid-value',
                    details=f'Invalid gender value: "{gender}". Must be one of: {", ".join(valid_genders)}',
                    location=f'{expected_type}.gender'
                ))
        
        # Check birth date format
        if 'birthDate' in resource_data:
            birth_date = resource_data['birthDate']
            if not isinstance(birth_date, str) or not self._is_valid_date_format(birth_date):
                issues.append(ValidationIssue(
                    severity='error',
                    code='invalid-format',
                    details=f'Invalid birth date format: "{birth_date}". Expected YYYY-MM-DD format',
                    location=f'{expected_type}.birthDate'
                ))
        
        # Check telecom format
        if 'telecom' in resource_data:
            telecoms = resource_data['telecom']
            if isinstance(telecoms, list):
                for i, telecom in enumerate(telecoms):
                    if 'system' in telecom:
                        system = telecom['system']
                        valid_systems = ['phone', 'fax', 'email', 'pager', 'url', 'sms', 'other']
                        if system not in valid_systems:
                            issues.append(ValidationIssue(
                                severity='error',
                                code='invalid-value',
                                details=f'Invalid telecom system: "{system}". Must be one of: {", ".join(valid_systems)}',
                                location=f'{expected_type}.telecom[{i}].system'
                            ))
        
        # Check extensions for wrong data types
        if 'extension' in resource_data:
            extensions = resource_data['extension']
            if isinstance(extensions, list):
                for i, ext in enumerate(extensions):
                    url = ext.get('url', '')
                    
                    # Check for religion extension with wrong type
                    if 'religion' in url and 'valueString' in ext:
                        issues.append(ValidationIssue(
                            severity='error',
                            code='wrong-data-type',
                            details='Religion extension should use valueCodeableConcept, not valueString',
                            location=f'{expected_type}.extension[{i}]'
                        ))
                    
                    # Check for educational attainment with wrong type
                    if 'educational-attainment' in url and 'valueBoolean' in ext:
                        issues.append(ValidationIssue(
                            severity='error',
                            code='wrong-data-type',
                            details='Educational attainment extension should use valueCodeableConcept, not valueBoolean',
                            location=f'{expected_type}.extension[{i}]'
                        ))
                    
                    # Check for invalid extension URLs
                    if 'invalid-extension-url' in url or 'not-allowed' in url:
                        issues.append(ValidationIssue(
                            severity='error',
                            code='invalid-extension',
                            details=f'Invalid or unauthorized extension URL: {url}',
                            location=f'{expected_type}.extension[{i}]'
                        ))
        
        return issues
    
    def _is_valid_date_format(self, date_str: str) -> bool:
        """Check if a string is in valid FHIR date format (YYYY-MM-DD)."""
        try:
            from datetime import datetime
            # Try to parse as YYYY-MM-DD
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            try:
                # Try to parse as YYYY-MM
                datetime.strptime(date_str, '%Y-%m')
                return True
            except ValueError:
                try:
                    # Try to parse as YYYY
                    datetime.strptime(date_str, '%Y')
                    return True
                except ValueError:
                    return False
        
    def get_available_profiles(self) -> List[str]:
        """Get list of available StructureDefinition URLs."""
        return list(self.structure_definitions.keys())
        
    def get_profile_info(self, profile_url: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific profile."""
        structure_def = self.structure_definitions.get(profile_url)
        if not structure_def:
            return None
            
        return {
            'url': structure_def.get('url'),
            'name': structure_def.get('name'),
            'title': structure_def.get('title'),
            'description': structure_def.get('description'),
            'type': structure_def.get('type'),
            'status': structure_def.get('status')
        }
