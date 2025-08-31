### wah4pc-validation-server: Language-Agnostic Usage Guide

This document explains how to use the PHCore FHIR Validation Server to validate FHIR resources for Philippine Core (PHCore) compliance before sending to downstream systems. The server runs locally at http://localhost:5072.

---

### Purpose and Typical Flow
- **Goal**: Ensure a source system’s FHIR resource is PHCore-compliant before transferring to a target system.
- **Recommended flow**:
  1) Source system constructs a FHIR R4 resource that conforms to a PHCore profile (e.g., Patient).
  2) Source system sends the resource to the validation server.
  3) Validation server returns an OperationOutcome indicating errors, warnings, or success.
  4) If no errors are returned, the source system proceeds to send the resource to the target system. If errors exist, the source system corrects the resource and revalidates.

---

### Base URL
- Base URL: `http://localhost:5072`
- All endpoints use JSON content. Clients should send and expect JSON payloads.

---

### Primary Validation Endpoint
- Path: `POST /ph-core/fhir/$validate`
- Purpose: Validate a single FHIR resource for PHCore compliance.
- Request formats (two options supported):
  - **Raw Resource**: Send the FHIR resource as the request body.
  - **Verbose Wrapper**: Send an object containing two members:
    - `resource`: the FHIR resource to validate
    - `verbose`: a boolean flag; when true, the server returns a comprehensive list of issues instead of only the first critical error
- Response: Always returns a FHIR `OperationOutcome` resource.
  - The server responds with HTTP 200 and includes issues in the OperationOutcome.
  - Validation result is determined by inspecting the OperationOutcome issues (see Interpretation Rules below).

---

### Interpretation Rules (OperationOutcome)
- The `OperationOutcome.issue` array contains one or more results.
- Each issue has at least:
  - `severity`: one of `error`, `warning`, `information`
  - `code`: a short machine-friendly indicator (e.g., `cardinality-min`, `type-mismatch`, `invalid-field`)
  - `details.text`: human-readable description
  - `location` (optional): element path related to the issue
- **Pass condition**: No issues with `severity = error`.
- **Fail condition**: One or more issues with `severity = error`.
- **Warnings** (`severity = warning`) do not block passing but indicate recommended improvements or missing non-critical terminologies.
- **Information** (`severity = information`) indicates successful validation or informational messages.

---

### Verbose vs Regular Validation
- **Regular mode** (default): The server focuses on the most critical PHCore compliance error and may stop reporting after the first blocking issue.
- **Verbose mode**: When `verbose` is set to true (via the verbose wrapper), the server continues validation and returns a comprehensive list of all detected issues.
- Recommended usage:
  - Use **regular mode** in production for fast feedback and gating.
  - Use **verbose mode** during development, testing, or when diagnosing complex failures.

---

### Profile Selection Behavior
- The validator automatically uses profiles declared in the resource’s `meta.profile` array when present.
- If no `meta.profile` is provided, the validator applies basic FHIR structure checks and available PHCore rules applicable without an explicit profile.
- For PHCore-compliant validation, include the appropriate PHCore profile URL in `meta.profile`.

---

### Additional Useful Endpoints
- `GET /` — Basic server information.
- `GET /ph-core/fhir/metadata` — Returns a FHIR `CapabilityStatement` describing the server’s capabilities.
- `GET /ph-core/fhir/profiles` — Lists available profile canonical URLs known to the server.
- Resource hosting (read-only access to hosted conformance/terminology artifacts and examples):
  - `GET /ph-core/fhir/StructureDefinition/{profile_id}`
  - `GET /ph-core/fhir/ValueSet/{valueset_id}`
  - `GET /ph-core/fhir/CodeSystem/{codesystem_id}`
  - `GET /ph-core/fhir/{resource_type}` — Returns resources of a given type known to the server.
  - `GET /ph-core/fhir/{resource_type}/{resource_id}` — Returns a specific resource by type and id.

---

### What the Validator Enforces
- **PHCore profile compliance**:
  - Resource type matches the profile’s `type`.
  - Required elements and cardinalities (e.g., required PHCore extensions such as `indigenous-people`).
  - Extension slicing rules (e.g., minimum occurrences of specific slices identified by canonical URLs).
- **Basic structure checks**: Required FHIR fields, basic format and type checks.
- **Terminology references**: ValueSet bindings and CodeSystem availability. The server hosts base HL7 FHIR R4 terminology; missing or unknown terminologies may appear as warnings.

---

### Integration Guidance (Source → Validator → Target)
1) **Assemble the resource** in the source system, ensuring it includes the PHCore `meta.profile` URL and required PHCore extensions.
2) **Send the resource to the validator** using `POST /ph-core/fhir/$validate`.
   - Use regular mode for gating in automated pipelines.
   - Use verbose mode to diagnose and fix all issues during development or QA.
3) **Interpret the OperationOutcome**:
   - If any `error` is present: block the transfer, fix the resource, revalidate.
   - If only `warning` or `information`: proceed (warnings are non-blocking), optionally log for later improvement.
4) **Transfer to target system** only after a pass (no `error` severity issues).
5) **Archive the OperationOutcome** with the transaction for auditability when required by policy.

---

### Operational Considerations
- **Environment**: Default host and port is `http://localhost:5072`.
- **Content Type**: Use JSON for requests and responses.
- **FHIR Version**: R4.
- **Profiles**: Philippine Core (PHCore) profiles are hosted; the server also includes base HL7 FHIR R4 artifacts for terminology and structure support.
- **Status Codes**: The server returns HTTP 200 with an OperationOutcome. Gate logic must inspect `OperationOutcome.issue[*].severity` for `error` to decide pass/fail.
- **Throughput & Size**: Validate one resource per request. For batch validation, callers should iterate resources and submit them individually.
- **Audit**: Store OperationOutcomes for compliance or troubleshooting.

---

### Troubleshooting and Common Results
- **cardinality-min** (error): A required element or extension is missing (e.g., required PHCore extension slice not present). Action: add the missing element and revalidate.
- **type-mismatch** (error): The resourceType does not match the profile’s expected type. Action: correct `resourceType` or the selected profile.
- **invalid-field / wrong-data-type / invalid-format** (error): Structural or format problems (e.g., wrong data type, invalid date format). Action: correct the offending field(s).
- **valueset-not-found** (warning): The referenced ValueSet is unknown to the server. Action: ensure the ValueSet is available; proceed if acceptable as this is non-blocking.
- **informational** (information): Indicates successful validation or general information.

---

### Minimal Checklist for Compliance
- The resource includes the proper PHCore `meta.profile` URL.
- All PHCore-required extensions (e.g., indigenous-people) are present and correctly formed.
- Identifiers, addresses, and coded elements follow PHCore and FHIR expectations (systems, codes, formats).
- Validation returns an OperationOutcome with no `error` severity issues.

---

### Support and Discovery
- Use `GET /ph-core/fhir/profiles` to discover what profiles are currently available.
- Use `GET /ph-core/fhir/metadata` to view capabilities.
- Use resource read endpoints to explore hosted StructureDefinitions, ValueSets, and CodeSystems.

This guide is implementation-language agnostic and focuses on how to interact with the validation server to gate PHCore-compliant data flows from source to target systems.
