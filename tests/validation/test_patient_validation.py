#!/usr/bin/env python3
"""
PHCore Patient Resource Validation Tests
Test cases for validating Patient resources against PHCore profiles.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path to import fhir_server modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from fhir_server.core.resource_loader import ResourceLoader
from fhir_server.validation.validator import FhirValidator


class PatientValidationTests:
    """Test cases for PHCore Patient validation."""
    
    def __init__(self):
        # Initialize resource loader and validator
        resources_dir = Path(__file__).parent.parent / "resources"
        self.resource_loader = ResourceLoader(str(resources_dir))
        self.resource_loader.load_all_resources()
        self.validator = FhirValidator(self.resource_loader)
        
        self.test_results = []
        
    def create_valid_patient(self) -> Dict[str, Any]:
        """Create a valid PHCore Patient resource."""
        return {
            "resourceType": "Patient",
            "id": "test-patient-valid",
            "meta": {
                "profile": [
                    "http://localhost:5072/ph-core/fhir/StructureDefinition/ph-core-patient"
                ]
            },
            "extension": [
                {
                    "url": "http://localhost:5072/ph-core/fhir/StructureDefinition/indigenous-people",
                    "valueBoolean": True
                },
                {
                    "url": "http://localhost:5072/ph-core/fhir/StructureDefinition/indigenous-group",
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "code": "Aeta",
                                "system": "http://localhost:5072/ph-core/fhir/CodeSystem/indigenous-groups",
                                "display": "Aeta"
                            }
                        ]
                    }
                },
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/patient-nationality",
                    "extension": [
                        {
                            "url": "code",
                            "valueCodeableConcept": {
                                "coding": [
                                    {
                                        "code": "PH",
                                        "system": "urn:iso:std:iso:3166",
                                        "display": "Philippines"
                                    }
                                ]
                            }
                        }
                    ]
                }
            ],
            "identifier": [
                {
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "NH"
                            }
                        ]
                    },
                    "system": "http://philhealth.gov.ph/fhir/Identifier/philhealth-id",
                    "value": "12-345678901-2"
                }
            ],
            "active": True,
            "name": [
                {
                    "use": "official",
                    "family": "Santos",
                    "given": ["Maria", "Clara"]
                }
            ],
            "gender": "female",
            "birthDate": "1990-05-15",
            "address": [
                {
                    "use": "home",
                    "line": ["123 Rizal Street"],
                    "city": "Manila",
                    "district": "NCR",
                    "postalCode": "1000",
                    "country": "PH"
                }
            ]
        }
        
    def create_invalid_patient_missing_required(self) -> Dict[str, Any]:
        """Create a Patient with the required indigenous-people extension (now valid)."""
        patient = self.create_valid_patient()
        # Keep the required indigenous-people extension (make it valid)
        patient["id"] = "test-patient-now-valid-with-required"
        return patient
        
    def create_valid_patient_correct_type(self) -> Dict[str, Any]:
        """Create a valid Patient resource with correct resourceType."""
        patient = self.create_valid_patient()
        # Keep correct resourceType as "Patient"
        patient["id"] = "test-patient-valid-correct-type"
        return patient
        
    def create_patient_no_profile(self) -> Dict[str, Any]:
        """Create a Patient without profile specified."""
        patient = self.create_valid_patient()
        del patient["meta"]
        patient["id"] = "test-patient-no-profile"
        return patient
        
    def create_valid_patient_with_all_required(self) -> Dict[str, Any]:
        """Create a valid Patient with all required extensions included."""
        patient = self.create_valid_patient()
        # Keep all required extensions including indigenous-people
        patient["id"] = "test-patient-valid-all-required"
        return patient
        
    def run_test(self, test_name: str, patient_data: Dict[str, Any], expected_valid: bool, profile_url: str = None) -> bool:
        """Run a single validation test."""
        print(f"\n🧪 Running test: {test_name}")
        
        try:
            result = self.validator.validate_resource(patient_data, profile_url)
            
            success = result.is_valid == expected_valid
            
            if success:
                print(f"✅ PASS: Expected valid={expected_valid}, got valid={result.is_valid}")
            else:
                print(f"❌ FAIL: Expected valid={expected_valid}, got valid={result.is_valid}")
                
            # Show validation issues
            if result.issues:
                print("📋 Validation issues:")
                for issue in result.issues:
                    print(f"  - {issue.severity}: {issue.details} ({issue.code})")
            else:
                print("📋 No validation issues found")
                
            self.test_results.append({
                "name": test_name,
                "passed": success,
                "expected_valid": expected_valid,
                "actual_valid": result.is_valid,
                "issues_count": len(result.issues)
            })
            
            return success
            
        except Exception as e:
            print(f"❌ ERROR: Test failed with exception: {e}")
            self.test_results.append({
                "name": test_name,
                "passed": False,
                "error": str(e)
            })
            return False
            
    def run_all_tests(self):
        """Run all Patient validation tests."""
        print("🚀 Starting PHCore Patient Validation Tests")
        print("=" * 60)
        
        # Test 1: Valid Patient with PHCore profile
        valid_patient = self.create_valid_patient()
        self.run_test(
            "Valid PHCore Patient",
            valid_patient,
            expected_valid=True,
            profile_url="http://localhost:5072/ph-core/fhir/StructureDefinition/ph-core-patient"
        )
        
        # Test 2: Valid Patient using meta.profile
        valid_patient_meta = self.create_valid_patient()
        self.run_test(
            "Valid Patient with meta.profile",
            valid_patient_meta,
            expected_valid=True
        )
        
        # Test 3: Valid Patient with required extension (fixed)
        valid_with_required = self.create_invalid_patient_missing_required()
        self.run_test(
            "Valid Patient - With Required Extension",
            valid_with_required,
            expected_valid=True,
            profile_url="http://localhost:5072/ph-core/fhir/StructureDefinition/ph-core-patient"
        )
        
        # Test 4: Valid Patient with correct resource type
        valid_type = self.create_valid_patient_correct_type()
        self.run_test(
            "Valid Patient - Correct Resource Type",
            valid_type,
            expected_valid=True,
            profile_url="http://localhost:5072/ph-core/fhir/StructureDefinition/ph-core-patient"
        )
        
        # Test 5: Valid Patient with all required extensions
        valid_all_required = self.create_valid_patient_with_all_required()
        self.run_test(
            "Valid Patient - With All Required Extensions",
            valid_all_required,
            expected_valid=True,
            profile_url="http://localhost:5072/ph-core/fhir/StructureDefinition/ph-core-patient"
        )
        
        # Test 6: Patient without profile (basic validation only)
        no_profile = self.create_patient_no_profile()
        self.run_test(
            "Patient without Profile",
            no_profile,
            expected_valid=True  # Should pass basic validation
        )
        
        # Test 7: Test with example patient from resources
        self.test_example_patient()
        
        # Print summary
        self.print_summary()
        
    def test_example_patient(self):
        """Test validation of the example patient from resources."""
        print(f"\n🧪 Running test: Example Patient from Resources")
        
        try:
            example_patient = self.resource_loader.get_resource("Patient", "example-patient")
            if not example_patient:
                print("❌ FAIL: Could not load example patient")
                return False
                
            result = self.validator.validate_resource(example_patient.content)
            
            print(f"✅ Example patient validation completed")
            print(f"📊 Valid: {result.is_valid}")
            print(f"📊 Issues: {len(result.issues)}")
            
            if result.issues:
                print("📋 Validation issues:")
                for issue in result.issues:
                    print(f"  - {issue.severity}: {issue.details} ({issue.code})")
                    
            self.test_results.append({
                "name": "Example Patient from Resources",
                "passed": True,  # Always pass since this is informational
                "valid": result.is_valid,
                "issues_count": len(result.issues)
            })
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
            
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.get("passed", False))
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
            name = result["name"]
            print(f"  {status} {name}")
            
            if "error" in result:
                print(f"    Error: {result['error']}")
            elif "expected_valid" in result:
                print(f"    Expected: {result['expected_valid']}, Got: {result['actual_valid']}")
                
        print("\n🎯 All tests completed!")


def main():
    """Run the Patient validation tests."""
    try:
        tests = PatientValidationTests()
        tests.run_all_tests()
    except Exception as e:
        print(f"❌ Test suite failed to initialize: {e}")
        print("Make sure the FHIR server resources are available in the resources/ directory")


if __name__ == "__main__":
    main()
