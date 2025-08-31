# FHIR Resource Examples

This directory contains example FHIR resources that demonstrate how external source systems (like hospital EMRs, clinic systems, etc.) would send data to our PHCore FHIR validation server.

## 📁 Example Structure

```
examples/
├── valid/                    # Valid FHIR resources that pass PHCore validation
│   ├── patient/             # Valid Patient resource examples
│   │   └── patient_from_hospital_emr.json
│   ├── encounter/           # Valid Encounter resource examples (future)
│   ├── observation/         # Valid Observation resource examples (future)
│   └── medication/          # Valid Medication resource examples (future)
├── invalid/                 # Invalid FHIR resources that fail validation
│   ├── patient/            # Invalid Patient resource examples
│   │   └── patient_missing_extension.json
│   ├── encounter/          # Invalid Encounter resource examples (future)
│   ├── observation/        # Invalid Observation resource examples (future)
│   └── medication/         # Invalid Medication resource examples (future)
└── README.md               # This documentation
```

## 🎯 Example Categories

### `valid/{resource_type}/`
**Valid FHIR Resources** - Examples that successfully pass PHCore validation, organized by resource type:

#### Patient Resources (`valid/patient/`)
- **`patient_from_hospital_emr.json`** - Complete, valid PHCore Patient resource
  - Includes all required PHCore extensions
  - Philippine-specific identifiers (PhilHealth, PhilSys, Hospital MRN)
  - Complete demographic and contact information
  - Proper address with PSGC codes
  - Emergency contact information

### `invalid/{resource_type}/`
**Invalid FHIR Resources** - Examples that demonstrate validation failures, organized by resource type:

#### Patient Resources (`invalid/patient/`)
- **`patient_missing_extension.json`** - Patient missing required `indigenous-people` extension
  - Demonstrates cardinality validation failure
  - Shows specific error reporting
  - Useful for testing error handling

## 🧪 Testing Examples

### Using the CLI Client
```bash
# Test valid patient examples
python client.py validate examples/valid/patient/patient_from_hospital_emr.json

# Test invalid patient examples  
python client.py validate examples/invalid/patient/patient_missing_extension.json

# Future: Test other resource types
# python client.py validate examples/valid/encounter/encounter_from_clinic.json
# python client.py validate examples/invalid/observation/observation_missing_code.json
```

### Using curl
```bash
# Test valid patient
curl -X POST "http://localhost:5072/ph-core/fhir/\$validate" \
  -H "Content-Type: application/json" \
  -d @examples/valid/patient/patient_from_hospital_emr.json

# Test invalid patient
curl -X POST "http://localhost:5072/ph-core/fhir/\$validate" \
  -H "Content-Type: application/json" \
  -d @examples/invalid/patient/patient_missing_extension.json
```

### Using Python directly
```python
import json
import requests

# Test valid patient example
with open('examples/valid/patient/patient_from_hospital_emr.json', 'r') as f:
    valid_patient = json.load(f)

response = requests.post(
    'http://localhost:5072/ph-core/fhir/$validate',
    json=valid_patient
)
print("Valid Patient Result:", response.json())

# Test invalid patient example
with open('examples/invalid/patient/patient_missing_extension.json', 'r') as f:
    invalid_patient = json.load(f)

response = requests.post(
    'http://localhost:5072/ph-core/fhir/$validate',
    json=invalid_patient
)
print("Invalid Patient Result:", response.json())
```

## 📊 Expected Results

### Valid Examples
```json
{
  "resourceType": "OperationOutcome",
  "issue": [
    {
      "severity": "information",
      "code": "informational",
      "details": {
        "text": "Resource validation completed successfully"
      }
    }
  ]
}
```

### Invalid Examples
```json
{
  "resourceType": "OperationOutcome",
  "issue": [
    {
      "severity": "error",
      "code": "cardinality-min",
      "details": {
        "text": "Extension slice 'indigenousPeople' requires minimum 1 occurrence(s), found 0. Expected URL: http://localhost:5072/ph-core/fhir/StructureDefinition/indigenous-people"
      },
      "location": ["Patient.extension:indigenousPeople"]
    }
  ]
}
```

## 🏗️ Creating New Examples

### Directory Structure Guidelines
1. **Choose the appropriate category**: `valid/` or `invalid/`
2. **Choose the resource type**: `patient/`, `encounter/`, `observation/`, etc.
3. **Use descriptive filenames**: Follow the naming conventions below

### For Valid Examples (`valid/{resource_type}/`)
1. **Follow PHCore Requirements**
   - Include all required extensions for the resource type
   - Use proper Philippine identifiers where applicable
   - Include complete address information with PSGC codes
   - Set appropriate `meta.profile` reference

2. **Use Realistic Data**
   - Philippine names and addresses
   - Valid PSGC codes for regions, provinces, cities
   - Appropriate contact information
   - Realistic medical data

3. **File Naming Convention**
   - Pattern: `{resource_type}_from_{source_system}.json`
   - Examples:
     - `patient_from_hospital_emr.json`
     - `patient_from_clinic_system.json`
     - `encounter_from_emergency_dept.json`
     - `observation_from_laboratory.json`

### For Invalid Examples (`invalid/{resource_type}/`)
1. **Focus on Specific Validation Issues**
   - Missing required extensions
   - Invalid data types
   - Incorrect cardinality
   - Wrong resource types
   - Terminology binding violations

2. **File Naming Convention**
   - Pattern: `{resource_type}_{validation_issue}.json`
   - Examples:
     - `patient_missing_extension.json`
     - `patient_invalid_identifier.json`
     - `encounter_wrong_status.json`
     - `observation_missing_code.json`

3. **Document the Issue**
   - Include comments explaining what makes the resource invalid
   - Reference specific PHCore requirements being violated

### Resource Type Examples

#### Patient Resources
```
examples/valid/patient/
├── patient_from_hospital_emr.json          # Complete hospital patient
├── patient_from_clinic_system.json         # Basic clinic patient  
├── patient_from_rural_health_unit.json     # Rural healthcare patient
└── patient_with_multiple_identifiers.json  # Patient with all ID types

examples/invalid/patient/
├── patient_missing_extension.json          # Missing required extension
├── patient_invalid_identifier.json         # Invalid identifier format
├── patient_wrong_address_format.json       # Incorrect address structure
└── patient_missing_required_fields.json    # Missing mandatory fields
```

#### Encounter Resources (Future)
```
examples/valid/encounter/
├── encounter_from_emergency_dept.json      # Emergency department visit
├── encounter_from_outpatient_clinic.json   # Outpatient consultation
└── encounter_from_inpatient_ward.json      # Hospital admission

examples/invalid/encounter/
├── encounter_invalid_status.json           # Invalid encounter status
├── encounter_missing_patient_ref.json      # Missing patient reference
└── encounter_wrong_class.json              # Invalid encounter class
```

## 🏥 Source System Integration by Resource Type

### Patient Resources
- **Hospital EMR Systems**: Complete demographics, insurance, emergency contacts
- **Clinic Management**: Basic patient info, appointment data
- **Laboratory Systems**: Patient identification for specimens
- **Pharmacy Systems**: Patient medication profiles

### Encounter Resources
- **Emergency Departments**: Urgent care visits, triage data
- **Outpatient Clinics**: Scheduled consultations, follow-ups
- **Inpatient Wards**: Hospital admissions, discharge planning

### Observation Resources
- **Laboratory Systems**: Test results, quality control
- **Vital Signs Monitoring**: Blood pressure, temperature, weight
- **Diagnostic Imaging**: Radiology findings, measurements

### Medication Resources
- **Pharmacy Systems**: Prescription dispensing, inventory
- **Hospital Formularies**: Medication administration records
- **Clinical Decision Support**: Drug interaction checking

## 🎨 Best Practices

1. **Hierarchical Organization**
   - Group by validation outcome first (`valid/` vs `invalid/`)
   - Then by resource type (`patient/`, `encounter/`, etc.)
   - Use consistent naming conventions throughout

2. **Data Quality**
   - Use realistic, culturally appropriate Philippine data
   - Follow Philippine naming conventions and geographic codes
   - Ensure examples represent real-world scenarios

3. **Coverage**
   - Create examples for all major PHCore resource types
   - Cover common validation scenarios and edge cases
   - Include examples from different healthcare settings

4. **Maintainability**
   - Keep examples focused on specific validation aspects
   - Document the purpose and expected outcome of each example
   - Regularly validate examples against current PHCore profiles

This deeply nested structure makes it easy for developers to find relevant examples for their specific resource type and validation scenario, while also providing a clear path for expanding the example collection as new resource types are added.
