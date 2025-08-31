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
        
        # Define valid fields for different resource types
        common_fields = ['resourceType', 'id', 'meta', 'implicitRules', 'language', 
                        'text', 'contained', 'extension', 'modifierExtension']
        
        valid_fields_by_type = {
            'Patient': common_fields + [
                'identifier', 'active', 'name', 'telecom', 'gender', 'birthDate',
                'address', 'maritalStatus', 'multipleBirthBoolean', 'multipleBirthInteger',
                'photo', 'contact', 'communication', 'generalPractitioner', 'managingOrganization', 'link'
            ],
            'Encounter': common_fields + [
                'identifier', 'status', 'statusHistory', 'class', 'classHistory', 'type',
                'serviceType', 'priority', 'subject', 'episodeOfCare', 'basedOn', 'participant',
                'appointment', 'period', 'length', 'reasonCode', 'reasonReference', 'diagnosis',
                'account', 'hospitalization', 'location', 'serviceProvider'
            ],
            'Observation': common_fields + [
                'identifier', 'basedOn', 'partOf', 'status', 'category', 'code', 'subject',
                'focus', 'encounter', 'effectiveDateTime', 'effectivePeriod', 'effectiveTiming',
                'effectiveInstant', 'issued', 'performer', 'valueQuantity', 'valueCodeableConcept',
                'valueString', 'valueBoolean', 'valueInteger', 'valueRange', 'valueRatio',
                'valueSampledData', 'valueTime', 'valueDateTime', 'valuePeriod', 'interpretation',
                'note', 'bodySite', 'method', 'specimen', 'device', 'referenceRange', 'hasMember',
                'derivedFrom', 'component'
            ],
            'Medication': common_fields + [
                'identifier', 'code', 'status', 'manufacturer', 'form', 'amount', 'ingredient',
                'batch', 'package'
            ]
        }
        
        # Get valid fields for this resource type, default to common fields only
        valid_fields = valid_fields_by_type.get(expected_type, common_fields)
        
        # Check for invalid fields
        invalid_fields = []
        for field_name in resource_data.keys():
            if field_name not in valid_fields:
                invalid_fields.append(field_name)
        
        for field in invalid_fields:
            issues.append(ValidationIssue(
                severity='error',
                code='invalid-field',
                details=f'Invalid field "{field}" found in {expected_type} resource',
                location=f'{expected_type}.{field}'
            ))
        
        # Resource-specific validation
        if expected_type == 'Patient':
            issues.extend(self._validate_patient_specific(resource_data))
        elif expected_type == 'Encounter':
            issues.extend(self._validate_encounter_specific(resource_data))
        elif expected_type == 'Medication':
            issues.extend(self._validate_medication_specific(resource_data))
        
        return issues
    
    def _validate_patient_specific(self, resource_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate Patient-specific structural issues."""
        issues = []
        
        # Check for invalid data types and formats
        if 'gender' in resource_data:
            gender = resource_data['gender']
            valid_genders = ['male', 'female', 'other', 'unknown']
            if gender not in valid_genders:
                issues.append(ValidationIssue(
                    severity='error',
                    code='invalid-value',
                    details=f'Invalid gender value: "{gender}". Must be one of: {", ".join(valid_genders)}',
                    location='Patient.gender'
                ))
        
        # Check birth date format
        if 'birthDate' in resource_data:
            birth_date = resource_data['birthDate']
            if not isinstance(birth_date, str) or not self._is_valid_date_format(birth_date):
                issues.append(ValidationIssue(
                    severity='error',
                    code='invalid-format',
                    details=f'Invalid birth date format: "{birth_date}". Expected YYYY-MM-DD format',
                    location='Patient.birthDate'
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
                                location=f'Patient.telecom[{i}].system'
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
                            location=f'Patient.extension[{i}]'
                        ))
                    
                    # Check for educational attainment with wrong type
                    if 'educational-attainment' in url and 'valueBoolean' in ext:
                        issues.append(ValidationIssue(
                            severity='error',
                            code='wrong-data-type',
                            details='Educational attainment extension should use valueCodeableConcept, not valueBoolean',
                            location=f'Patient.extension[{i}]'
                        ))
                    
                    # Check for invalid extension URLs
                    if 'invalid-extension-url' in url or 'not-allowed' in url:
                        issues.append(ValidationIssue(
                            severity='error',
                            code='invalid-extension',
                            details=f'Invalid or unauthorized extension URL: {url}',
                            location=f'Patient.extension[{i}]'
                        ))
        
        return issues
    
    def _validate_encounter_specific(self, resource_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate Encounter-specific structural issues."""
        issues = []
        
        # Check encounter status
        if 'status' in resource_data:
            status = resource_data['status']
            valid_statuses = ['planned', 'arrived', 'triaged', 'in-progress', 'onleave', 'finished', 'cancelled', 'entered-in-error', 'unknown']
            if status not in valid_statuses:
                issues.append(ValidationIssue(
                    severity='error',
                    code='invalid-value',
                    details=f'Invalid encounter status: "{status}". Must be one of: {", ".join(valid_statuses)}',
                    location='Encounter.status'
                ))
        
        # Check class structure
        if 'class' in resource_data:
            encounter_class = resource_data['class']
            if isinstance(encounter_class, str):
                issues.append(ValidationIssue(
                    severity='error',
                    code='wrong-data-type',
                    details='Encounter.class should be a Coding object, not a string',
                    location='Encounter.class'
                ))
        
        # Check type structure
        if 'type' in resource_data:
            encounter_type = resource_data['type']
            if isinstance(encounter_type, str):
                issues.append(ValidationIssue(
                    severity='error',
                    code='wrong-data-type',
                    details='Encounter.type should be an array of CodeableConcept, not a string',
                    location='Encounter.type'
                ))
        
        # Check subject structure
        if 'subject' in resource_data:
            subject = resource_data['subject']
            if isinstance(subject, str):
                issues.append(ValidationIssue(
                    severity='error',
                    code='wrong-data-type',
                    details='Encounter.subject should be a Reference object, not a string',
                    location='Encounter.subject'
                ))
        
        # Check period dates
        if 'period' in resource_data:
            period = resource_data['period']
            if isinstance(period, dict):
                for field in ['start', 'end']:
                    if field in period:
                        date_value = period[field]
                        if not self._is_valid_datetime_format(date_value):
                            issues.append(ValidationIssue(
                                severity='error',
                                code='invalid-format',
                                details=f'Invalid period.{field} format: "{date_value}". Expected ISO 8601 datetime format',
                                location=f'Encounter.period.{field}'
                            ))
        
        return issues
    
    def _validate_medication_specific(self, resource_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate Medication-specific structural issues."""
        issues = []
        
        # Check medication status
        if 'status' in resource_data:
            status = resource_data['status']
            valid_statuses = ['active', 'inactive', 'entered-in-error']
            if status not in valid_statuses:
                issues.append(ValidationIssue(
                    severity='error',
                    code='invalid-value',
                    details=f'Invalid medication status: "{status}". Must be one of: {", ".join(valid_statuses)}',
                    location='Medication.status'
                ))
        
        # Check code structure
        if 'code' in resource_data:
            code = resource_data['code']
            if isinstance(code, str):
                issues.append(ValidationIssue(
                    severity='error',
                    code='wrong-data-type',
                    details='Medication.code should be a CodeableConcept object, not a string',
                    location='Medication.code'
                ))
        
        # Check manufacturer structure
        if 'manufacturer' in resource_data:
            manufacturer = resource_data['manufacturer']
            if isinstance(manufacturer, str):
                issues.append(ValidationIssue(
                    severity='error',
                    code='wrong-data-type',
                    details='Medication.manufacturer should be a Reference object, not a string',
                    location='Medication.manufacturer'
                ))
        
        # Check form structure
        if 'form' in resource_data:
            form = resource_data['form']
            if isinstance(form, list) and all(isinstance(item, str) for item in form):
                issues.append(ValidationIssue(
                    severity='error',
                    code='wrong-data-type',
                    details='Medication.form should be a CodeableConcept object, not an array of strings',
                    location='Medication.form'
                ))
        
        # Check amount structure
        if 'amount' in resource_data:
            amount = resource_data['amount']
            if isinstance(amount, dict):
                if 'numerator' in amount:
                    numerator = amount['numerator']
                    if isinstance(numerator, dict) and 'value' in numerator:
                        value = numerator['value']
                        if isinstance(value, str):
                            issues.append(ValidationIssue(
                                severity='error',
                                code='wrong-data-type',
                                details='Medication.amount.numerator.value should be a number, not a string',
                                location='Medication.amount.numerator.value'
                            ))
                if 'denominator' in amount:
                    denominator = amount['denominator']
                    if isinstance(denominator, str):
                        issues.append(ValidationIssue(
                            severity='error',
                            code='wrong-data-type',
                            details='Medication.amount.denominator should be a Quantity object, not a string',
                            location='Medication.amount.denominator'
                        ))
        
        # Check ingredient structure
        if 'ingredient' in resource_data:
            ingredients = resource_data['ingredient']
            if isinstance(ingredients, list):
                for i, ingredient in enumerate(ingredients):
                    if 'itemString' in ingredient:
                        issues.append(ValidationIssue(
                            severity='error',
                            code='wrong-data-type',
                            details='Medication ingredient should use itemCodeableConcept, not itemString',
                            location=f'Medication.ingredient[{i}]'
                        ))
                    
                    if 'strength' in ingredient:
                        strength = ingredient['strength']
                        if isinstance(strength, str):
                            issues.append(ValidationIssue(
                                severity='error',
                                code='wrong-data-type',
                                details='Medication ingredient strength should be a Ratio object, not a string',
                                location=f'Medication.ingredient[{i}].strength'
                            ))
                        elif isinstance(strength, dict):
                            if 'numerator' in strength:
                                numerator = strength['numerator']
                                if isinstance(numerator, dict) and 'value' in numerator:
                                    value = numerator['value']
                                    if isinstance(value, str) or (isinstance(value, (int, float)) and value < 0):
                                        issues.append(ValidationIssue(
                                            severity='error',
                                            code='invalid-value',
                                            details=f'Invalid strength numerator value: "{value}". Must be a positive number',
                                            location=f'Medication.ingredient[{i}].strength.numerator.value'
                                        ))
                            if 'denominator' in strength:
                                denominator = strength['denominator']
                                if isinstance(denominator, dict) and 'value' in denominator:
                                    value = denominator['value']
                                    if isinstance(value, str):
                                        issues.append(ValidationIssue(
                                            severity='error',
                                            code='wrong-data-type',
                                            details='Medication ingredient strength denominator value should be a number, not a string',
                                            location=f'Medication.ingredient[{i}].strength.denominator.value'
                                        ))
        
        # Check batch structure
        if 'batch' in resource_data:
            batch = resource_data['batch']
            if isinstance(batch, dict):
                if 'lotNumber' in batch:
                    lot_number = batch['lotNumber']
                    if not isinstance(lot_number, str):
                        issues.append(ValidationIssue(
                            severity='error',
                            code='wrong-data-type',
                            details=f'Medication batch lotNumber should be a string, not {type(lot_number).__name__}',
                            location='Medication.batch.lotNumber'
                        ))
                if 'expirationDate' in batch:
                    expiration_date = batch['expirationDate']
                    if not isinstance(expiration_date, str) or not self._is_valid_date_format(expiration_date):
                        issues.append(ValidationIssue(
                            severity='error',
                            code='invalid-format',
                            details=f'Invalid expiration date format: "{expiration_date}". Expected YYYY-MM-DD format',
                            location='Medication.batch.expirationDate'
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
        
    def _is_valid_datetime_format(self, date_str: str) -> bool:
        """Check if a string is in valid FHIR datetime format (YYYY-MM-DDThh:mm:ss.sss+zz:zz)."""
        try:
            from datetime import datetime
            # Try to parse as YYYY-MM-DDThh:mm:ss.sss+zz:zz
            datetime.fromisoformat(date_str)
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
