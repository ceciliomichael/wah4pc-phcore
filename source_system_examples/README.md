# Source System Examples for PHCore FHIR Validation

This folder contains realistic FHIR Patient resources that represent what Philippine healthcare systems would send for validation against the PHCore implementation guide.

## 📁 Files

### ✅ Valid Examples
- **`patient_from_hospital_emr.json`** - Complete valid Patient from Philippine General Hospital EMR
  - Includes all required PHCore extensions
  - Comprehensive demographic and contact information
  - Philippine-specific identifiers (PhilHealth, PhilSys, Hospital MRN)
  - Proper address with PSGC codes
  - Emergency contact information

### ❌ Invalid Examples  
- **`invalid_patient_missing_extension.json`** - Patient missing required indigenous-people extension
  - Demonstrates validation failure
  - Shows what happens when PHCore requirements are not met

## 🧪 How to Test These Examples

### Method 1: Using CLI Client
```bash
# Test valid patient
python client.py validate source_system_examples/patient_from_hospital_emr.json

# Test invalid patient  
python client.py validate source_system_examples/invalid_patient_missing_extension.json
```

### Method 2: Using curl (with server running)
```bash
# Start the validation server first
python main.py

# Test valid patient
curl -X POST 'http://localhost:5072/ph-core/fhir/$validate' \
  -H 'Content-Type: application/json' \
  -d @source_system_examples/patient_from_hospital_emr.json

# Test invalid patient
curl -X POST 'http://localhost:5072/ph-core/fhir/$validate' \
  -H 'Content-Type: application/json' \
  -d @source_system_examples/invalid_patient_missing_extension.json
```

### Method 3: Using Python Script
```python
import json
from client import FhirValidationClient

client = FhirValidationClient()

# Load and validate patient
with open('source_system_examples/patient_from_hospital_emr.json') as f:
    patient = json.load(f)
    
result = client.validate_resource(patient)
print(json.dumps(result, indent=2))
```

## 🏥 What These Examples Represent

### Valid Patient Example
**Ana Marie Reyes Santos** - A comprehensive patient record from Philippine General Hospital:
- **Demographics**: 39-year-old Filipino female nurse
- **Identifiers**: PhilHealth ID, PhilSys ID, Hospital MRN
- **Address**: Complete Philippine address with PSGC codes (Quezon City, NCR)
- **Extensions**: All required PHCore extensions including indigenous-people status
- **Contact**: Emergency contact information
- **Languages**: Tagalog (preferred) and English

### Invalid Patient Example
**Jose Rizal Garcia** - A patient record from Rural Health Unit with validation issues:
- **Missing**: Required indigenous-people extension
- **Source**: Rural Health Unit EMR System (demonstrates different source systems)
- **Location**: Cebu City (demonstrates provincial healthcare)
- **Language**: Cebuano and English

## 🎯 Expected Validation Results

### Valid Patient
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

### Invalid Patient
```json
{
  "resourceType": "OperationOutcome",
  "issue": [
    {
      "severity": "error",
      "code": "cardinality-min",
      "details": {
        "text": "Extension slice 'indigenousPeople' requires minimum 1 occurrence(s), found 0"
      },
      "location": ["Patient.extension:indigenousPeople"]
    }
  ]
}
```

## 🏗️ Creating Your Own Examples

When creating Patient resources for PHCore validation, ensure you include:

### Required Elements
- ✅ `resourceType: "Patient"`
- ✅ `meta.profile` pointing to PHCore Patient profile
- ✅ `extension` with required `indigenous-people` extension (min: 1)
- ✅ Proper `identifier` with system and value

### Recommended Elements
- 📋 Philippine-specific identifiers (PhilHealth, PhilSys)
- 📋 Complete address with PSGC extensions
- 📋 Nationality, religion, race extensions
- 📋 Occupation and educational attainment
- 📋 Emergency contact information
- 📋 Communication languages

## 🚀 Integration with Source Systems

These examples demonstrate how real Philippine healthcare systems can integrate with the PHCore validation server:

1. **Hospital EMRs** - Validate patient registration data
2. **Clinic Systems** - Check patient demographics before submission
3. **Laboratory Systems** - Ensure patient references are valid
4. **Insurance Systems** - Validate patient data for claims processing

The validation server acts as a quality gate ensuring all patient data meets PHCore implementation guide standards before being used in the Philippine healthcare ecosystem.
