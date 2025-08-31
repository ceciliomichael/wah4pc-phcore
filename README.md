# PHCore FHIR Validation Server

A comprehensive FHIR validation server implementation for the Philippine Core (PHCore) Implementation Guide, providing validation services for healthcare interoperability in the Philippines.

## 🏗️ Project Structure

```
wah4pc-phcore/
├── fhir_server/           # Core server implementation
│   ├── api/               # FastAPI REST endpoints
│   ├── core/              # Resource loading and management
│   └── validation/        # FHIR validation logic
├── resources/             # FHIR resource definitions
│   ├── phcore/           # PHCore implementation guide resources
│   └── fhir_base/        # Base FHIR R4 specification resources
├── examples/              # Sample FHIR resources for testing
│   ├── valid/            # Valid resources by type (patient/, encounter/, etc.)
│   └── invalid/          # Invalid resources by type (patient/, encounter/, etc.)
├── tests/                 # Test suites and validation tests
│   ├── validation/       # FHIR validation-specific tests
│   └── integration/      # End-to-end integration tests
├── scripts/               # Utility scripts
├── client.py              # CLI client for testing
├── main.py               # Server entry point
└── requirements.txt       # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip (Python package manager)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd wah4pc-phcore

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download base FHIR resources (if not already present)
python scripts/download_fhir_base.py
```

### Running the Server
```bash
python main.py
```

The server will start on `http://localhost:5072`

## 📡 API Endpoints

### Core Endpoints
- `GET /` - Server information
- `GET /ph-core/fhir/metadata` - FHIR CapabilityStatement
- `POST /ph-core/fhir/$validate` - Validate FHIR resources

### Resource Access
- `GET /ph-core/fhir/profiles` - List available profiles
- `GET /ph-core/fhir/{resource_type}` - Get resources by type
- `GET /ph-core/fhir/{resource_type}/{id}` - Get specific resource
- `GET /ph-core/fhir/StructureDefinition/{profile_id}` - Get profile definition
- `GET /ph-core/fhir/ValueSet/{valueset_id}` - Get value set
- `GET /ph-core/fhir/CodeSystem/{codesystem_id}` - Get code system

## 🧪 Testing

### Using the CLI Client
```bash
# Validate a FHIR resource
python client.py validate examples/valid/patient/patient_from_hospital_emr.json

# List available profiles
python client.py profiles

# Get a specific resource
python client.py resource StructureDefinition ph-core-patient
```

### Using curl
```bash
# Validate resource
curl -X POST "http://localhost:5072/ph-core/fhir/\$validate" \
  -H "Content-Type: application/json" \
  -d @examples/valid/patient/patient_from_hospital_emr.json

# Get server metadata
curl "http://localhost:5072/ph-core/fhir/metadata"
```

### Running Test Suite
```bash
# Run patient validation tests
python tests/test_patient_validation.py

# Run proof validation tests  
python tests/test_proof_validation_works.py
```

## 📁 Directory Details

### `fhir_server/`
Core server implementation with modular architecture:
- **`api/`** - FastAPI REST API endpoints and request/response handling
- **`core/`** - Resource loading, indexing, and management utilities
- **`validation/`** - FHIR validation engine with PHCore profile support

### `resources/`
FHIR resource definitions organized by source:
- **`phcore/`** - Philippine Core Implementation Guide resources (61 files)
- **`fhir_base/`** - Official HL7 FHIR R4 specification resources (11,322 resources)

### `examples/`
Sample FHIR resources organized by validation outcome and resource type:
- **`valid/{resource_type}/`** - FHIR resources that pass PHCore validation
- **`invalid/{resource_type}/`** - FHIR resources that fail validation  
- Hierarchical organization by resource type (patient, encounter, observation, etc.)
- Comprehensive README with testing instructions and best practices

### `tests/`
Comprehensive test suites:
- Patient resource validation tests (7 test cases)
- Proof validation tests demonstrating validation engine functionality

### `scripts/`
Utility scripts for project maintenance:
- FHIR base resource downloader from HL7 website

## 🔍 Validation Features

### PHCore Profile Validation
- ✅ Structure definition compliance checking
- ✅ Extension slice validation with cardinality enforcement
- ✅ Required field validation
- ✅ Data type and format validation

### Terminology Validation
- ✅ ValueSet binding validation
- ✅ CodeSystem reference checking
- ✅ Standard FHIR terminology support

### Error Reporting
- ✅ Detailed OperationOutcome responses
- ✅ Specific error locations and descriptions
- ✅ Severity levels (error, warning, information)

## 🌐 Interoperability

This server provides:
- **FHIR R4 compliance** - Full adherence to HL7 FHIR R4 standard
- **PHCore validation** - Philippine healthcare context validation
- **REST API** - Standard FHIR REST endpoints
- **Terminology services** - ValueSet and CodeSystem hosting
- **Resource hosting** - Complete implementation guide resource access

## 🏥 Use Cases

### Healthcare Systems Integration
- Hospital EMR validation before data submission
- Clinic system PHCore compliance checking
- Laboratory result format validation
- Insurance claim data verification

### Implementation Guide Testing
- Profile definition validation
- Extension usage verification
- Terminology binding testing
- Interoperability compliance checking

## 📊 Resource Statistics

- **PHCore Resources**: 61 files
- **Base FHIR Resources**: 11,322 resources
- **StructureDefinitions**: 7,454 (including PHCore profiles)
- **ValueSets**: 1,324 (including Philippine terminologies)
- **CodeSystems**: 1,067 (including PSGC, PSOC, PSCED)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project implements the Philippine Core Implementation Guide for FHIR and is intended for healthcare interoperability in the Philippines.

## 🆘 Support

For issues, questions, or contributions:
- Check the `examples/` directory for usage examples
- Review the `tests/` directory for validation scenarios
- Use the CLI client for interactive testing
- Examine server logs for debugging information
