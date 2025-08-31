# Test Suite

This directory contains comprehensive test suites for the PHCore FHIR validation server, organized by test type and functionality.

## 📁 Test Structure

```
tests/
├── validation/           # FHIR validation-specific tests
│   └── test_patient_validation.py
├── integration/         # End-to-end integration tests
│   └── test_proof_validation_works.py
└── README.md           # This documentation
```

## 🧪 Test Categories

### `validation/`
**FHIR Validation Tests** - Tests focused on the validation engine functionality:
- **`test_patient_validation.py`** - Comprehensive PHCore Patient resource validation tests
  - 7 test cases covering valid and invalid scenarios
  - Extension slice validation testing
  - Profile compliance checking
  - Cardinality enforcement verification

### `integration/`
**Integration Tests** - End-to-end tests that verify the complete system functionality:
- **`test_proof_validation_works.py`** - Proof tests demonstrating the validation engine works correctly
  - Valid vs invalid resource differentiation
  - Complete validation workflow testing
  - System integration verification

## 🚀 Running Tests

### Run All Tests
```bash
# Run all validation tests
python tests/validation/test_patient_validation.py

# Run all integration tests
python tests/integration/test_proof_validation_works.py
```

### Run Specific Test Categories
```bash
# Run patient validation tests only
python tests/validation/test_patient_validation.py

# Run proof validation tests only
python tests/integration/test_proof_validation_works.py
```

## 📊 Test Coverage

### Validation Tests (`validation/`)
- ✅ **Patient Resource Validation** (7 test cases)
  - Valid PHCore Patient with all required elements
  - Valid Patient with meta.profile declaration
  - Valid Patient with required extensions
  - Invalid Patient with wrong resource type
  - Invalid Patient missing required extensions
  - Patient without profile specification
  - Example Patient from PHCore resources

### Integration Tests (`integration/`)
- ✅ **End-to-End Validation Workflow**
  - Valid Patient resource processing
  - Invalid Patient resource detection
  - Complete validation engine functionality
  - System integration verification

## 🎯 Test Results

### Expected Outcomes

#### Validation Tests
- **Success Rate**: 100% (7/7 tests passing)
- **Coverage**: All major Patient validation scenarios
- **Validation**: Extension slices, cardinality, profile compliance

#### Integration Tests  
- **Valid Patient**: Should return `valid=True` with no issues
- **Invalid Patient**: Should return `valid=False` with specific error details
- **System Integration**: Complete validation workflow verification

## 📝 Adding New Tests

### For Validation Tests (`validation/`)
1. Create test files following the pattern: `test_{resource_type}_validation.py`
2. Include both valid and invalid scenarios
3. Test specific validation rules and edge cases
4. Follow the existing test structure and naming conventions

### For Integration Tests (`integration/`)
1. Create test files following the pattern: `test_{functionality}_integration.py`
2. Focus on end-to-end workflows
3. Test complete system functionality
4. Verify integration between different components

### Test File Template
```python
#!/usr/bin/env python3
"""
Test Description
Tests for [specific functionality]
"""

from fhir_server.core.resource_loader import ResourceLoader
from fhir_server.validation.validator import FhirValidator

def main():
    """Run the test suite."""
    # Load resources
    loader = ResourceLoader()
    loader.load_all_resources()
    validator = FhirValidator(loader)
    
    # Test cases here
    print("🧪 Running [Test Name]")
    # ... test implementation
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    main()
```

## 🔍 Debugging Tests

### Common Issues
- **Resource Loading**: Ensure PHCore and base FHIR resources are properly loaded
- **Path Issues**: Verify file paths are correct after project reorganization
- **Validation Logic**: Check that validation rules match PHCore requirements

### Debug Information
- Tests output detailed validation results including specific error messages
- Use the `📋 Validation issues:` section in test output to understand failures
- Check server logs when running integration tests

## 🎨 Test Output Format

Tests use emoji-rich output for better readability:
- 🚀 Test suite start
- 🧪 Individual test execution
- ✅ Test pass
- ❌ Test fail
- 📋 Validation details
- 📊 Summary statistics

This format makes it easy to quickly identify test results and issues during development and CI/CD processes.
