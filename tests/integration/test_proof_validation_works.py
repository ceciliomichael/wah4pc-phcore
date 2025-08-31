#!/usr/bin/env python3
"""
Proof Test: Demonstrate that validation actually works by creating an invalid Patient
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fhir_server.core.resource_loader import ResourceLoader
from fhir_server.validation.validator import FhirValidator


def main():
    print("🔍 PROOF TEST: Demonstrating Real Validation")
    print("=" * 50)
    
    # Load resources and create validator
    resources_dir = Path(__file__).parent.parent / "resources"
    resource_loader = ResourceLoader(str(resources_dir))
    resource_loader.load_all_resources()
    validator = FhirValidator(resource_loader)
    
    # Create an INTENTIONALLY INVALID Patient (missing required extension)
    invalid_patient = {
        "resourceType": "Patient",
        "id": "proof-test-invalid",
        "meta": {
            "profile": [
                "http://localhost:5072/ph-core/fhir/StructureDefinition/ph-core-patient"
            ]
        },
        # DELIBERATELY MISSING the required indigenous-people extension
        "name": [{"family": "Test", "given": ["Invalid"]}],
        "gender": "male"
    }
    
    print("🧪 Testing INVALID Patient (missing required indigenous-people extension)")
    result = validator.validate_resource(invalid_patient)
    
    print(f"📊 Valid: {result.is_valid}")
    print(f"📊 Issues Found: {len(result.issues)}")
    
    if result.issues:
        print("📋 Validation Issues:")
        for issue in result.issues:
            print(f"  - {issue.severity}: {issue.details}")
    
    # Now test with VALID Patient
    print("\n" + "-" * 50)
    print("🧪 Testing VALID Patient (with required extension)")
    
    valid_patient = {
        "resourceType": "Patient",
        "id": "proof-test-valid",
        "meta": {
            "profile": [
                "http://localhost:5072/ph-core/fhir/StructureDefinition/ph-core-patient"
            ]
        },
        "extension": [
            {
                "url": "http://localhost:5072/ph-core/fhir/StructureDefinition/indigenous-people",
                "valueBoolean": False
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
        "name": [{"family": "Test", "given": ["Valid"]}],
        "gender": "female"
    }
    
    result2 = validator.validate_resource(valid_patient)
    
    print(f"📊 Valid: {result2.is_valid}")
    print(f"📊 Issues Found: {len(result2.issues)}")
    
    if result2.issues:
        print("📋 Validation Issues:")
        for issue in result2.issues:
            print(f"  - {issue.severity}: {issue.details}")
    else:
        print("📋 No validation issues found")
    
    print("\n🎯 PROOF COMPLETE:")
    print(f"  Invalid Patient: Valid={result.is_valid} (should be False)")
    print(f"  Valid Patient: Valid={result2.is_valid} (should be True)")
    
    if not result.is_valid and result2.is_valid:
        print("✅ VALIDATION IS REAL AND WORKING!")
    else:
        print("❌ Something is wrong with validation")


if __name__ == "__main__":
    main()
