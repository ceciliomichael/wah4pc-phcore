# PHCore FHIR Playground

A comprehensive interactive testing environment for the Philippine Core (PHCore) Implementation Guide, providing developers with powerful tools for FHIR resource validation, exploration, and documentation.

## 🌟 Overview

The PHCore FHIR Playground is a web-based application that integrates seamlessly with the PHCore FHIR validation server, offering an intuitive interface for:

- **Real-time FHIR Resource Validation** - Validate resources against PHCore profiles with instant feedback
- **Interactive Example Browser** - Explore valid and invalid FHIR resources organized by type
- **Comprehensive Documentation** - Access detailed guides, API references, and troubleshooting tips
- **Developer-Friendly Interface** - Modern flat UI design with keyboard shortcuts and accessibility features

## 🏗️ Architecture

The playground follows a modular architecture with clear separation of concerns:

```
playground/
├── __init__.py           # Module initialization
├── app.py               # Core application logic and PlaygroundApp class
├── routes.py            # FastAPI route handlers and API endpoints
├── templates/           # Jinja2 HTML templates
│   ├── playground.html  # Main playground interface
│   ├── docs.html       # Documentation page
│   ├── examples.html   # Examples browser (future)
│   └── validator.html  # Dedicated validator (future)
├── static/             # Static assets
│   ├── css/
│   │   └── playground.css  # Comprehensive styling
│   └── js/
│       └── playground.js   # Interactive functionality
└── README.md           # This documentation
```

## 🚀 Features

### Core Functionality

#### 1. Real-time Validation Engine
- **Dual Validation Modes**: Quick mode for fast feedback, verbose mode for comprehensive analysis
- **PHCore Profile Compliance**: Validates against all Philippine Core StructureDefinitions
- **Detailed Error Reporting**: Clear, actionable error messages with location information
- **Progress Indicators**: Visual feedback during validation operations

#### 2. Interactive Resource Editor
- **Syntax Highlighting**: JSON editor with proper formatting
- **Auto-resize**: Dynamic textarea that grows with content
- **Keyboard Shortcuts**: Efficient workflow with shortcuts
- **Example Loading**: One-click loading of sample resources

#### 3. Comprehensive Examples Library
- **Organized by Validity**: Separate valid and invalid examples
- **Resource Type Grouping**: Examples organized by FHIR resource type
- **Detailed Descriptions**: Clear descriptions for each example
- **Real-world Scenarios**: Examples based on Philippine healthcare use cases

#### 4. Documentation System
- **Getting Started Guide**: Step-by-step instructions for new users
- **Feature Overview**: Detailed explanation of all capabilities
- **Validation Guide**: How to understand and fix validation issues
- **API Reference**: Complete programmatic access documentation
- **Troubleshooting**: FAQ and common issue solutions

### User Interface Features

#### Design Principles
- **Flat UI Design**: Clean, modern aesthetic with subtle 3D elements
- **OKLCH Color Space**: Perceptually uniform colors for better accessibility
- **Responsive Layout**: Full viewport height with desktop-first responsive design
- **Shadow Depth**: Strategic use of shadows to create visual hierarchy

#### Interactive Elements
- **Hover Effects**: Smooth transitions and visual feedback
- **Loading States**: Clear progress indicators for async operations
- **Notifications**: Toast-style notifications for user feedback
- **Keyboard Navigation**: Full keyboard accessibility support

## 📡 API Reference

### Validation Endpoints

#### POST `/playground/api/validate`
Validate a FHIR resource against PHCore profiles.

**Request Body:**
```json
{
  "resource": {
    "resourceType": "Patient",
    "id": "example",
    // ... FHIR resource content
  },
  "verbose": false
}
```

**Response:**
```json
{
  "success": true,
  "issues": [],
  "total_issues": 0,
  "error_count": 0,
  "warning_count": 0
}
```

#### POST `/playground/api/validate-example`
Form-based validation endpoint for HTML forms.

**Form Data:**
- `example_data`: JSON string of FHIR resource
- `verbose`: Boolean for verbose validation

### Examples Endpoints

#### GET `/playground/api/examples/{validity}/{resource_type}`
Get examples by validity and resource type.

**Parameters:**
- `validity`: "valid" or "invalid"
- `resource_type`: FHIR resource type (e.g., "patient", "encounter")

**Response:**
```json
[
  {
    "filename": "patient_example.json",
    "filepath": "examples/valid/patient/patient_example.json",
    "data": { /* FHIR resource */ },
    "description": "Patient: John Doe (ID: example)"
  }
]
```

#### GET `/playground/api/example/{validity}/{resource_type}/{filename}`
Get a specific example by validity, resource type, and filename.

### Profile Endpoints

#### GET `/playground/api/profiles`
Get available PHCore profiles.

**Response:**
```json
{
  "profiles": [
    {
      "name": "PHCore Patient Profile",
      "url": "https://fhir.ph/core/StructureDefinition/ph-core-patient",
      "version": "1.0.0",
      "description": "Patient profile for Philippine Core"
    }
  ]
}
```

#### GET `/playground/api/profile/{profile_id}`
Get specific profile information.

## 🎨 Styling Guide

### Color Palette (OKLCH)

The playground uses a carefully crafted color palette in OKLCH color space:

- **Primary Blue**: `oklch(65% 0.15 220)` - Main brand color
- **Success Green**: `oklch(65% 0.15 130)` - Success states
- **Warning Orange**: `oklch(70% 0.15 60)` - Warning states  
- **Error Red**: `oklch(65% 0.15 15)` - Error states
- **Neutral Gray**: `oklch(50% 0.01 210)` - Text and borders
- **Background**: `oklch(97% 0.01 210)` - Main background
- **Surface**: `oklch(100% 0 0)` - Card and surface backgrounds

### Typography

- **Font Family**: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif
- **Code Font**: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace
- **Font Sizes**: 16px base, responsive scaling
- **Line Height**: 1.6 for optimal readability

### Layout System

- **Container**: Max-width 1200px, centered with padding
- **Grid System**: CSS Grid for responsive layouts
- **Spacing**: 8px base unit with consistent scaling
- **Border Radius**: 8px for buttons, 12px for cards

## 🔧 Development Guide

### Setting Up Development Environment

1. **Prerequisites**
   ```bash
   # Ensure you have Python 3.11+ installed
   python --version
   ```

2. **Install Dependencies**
   ```bash
   # Install required packages
   pip install fastapi uvicorn jinja2 python-multipart
   ```

3. **Directory Structure**
   ```bash
   # Ensure proper directory structure exists
   mkdir -p playground/templates playground/static/css playground/static/js
   ```

### Adding New Features

#### 1. Adding New Routes
Edit `playground/routes.py`:

```python
@app.get("/playground/new-feature")
async def new_feature(request: Request):
    """New feature route."""
    return playground_app.templates.TemplateResponse("new_feature.html", {
        "request": request,
        "title": "New Feature"
    })
```

#### 2. Adding New Templates
Create new template in `playground/templates/`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="/playground/static/css/playground.css">
</head>
<body>
    <!-- Template content -->
</body>
</html>
```

#### 3. Adding New Styles
Add to `playground/static/css/playground.css`:

```css
/* New feature styles */
.new-feature {
    background: oklch(100% 0 0);
    border-radius: 12px;
    padding: 1.5rem;
}
```

#### 4. Adding JavaScript Functionality
Add to `playground/static/js/playground.js`:

```javascript
/**
 * New feature functionality
 */
function newFeature() {
    // Implementation
}

// Add to global API
window.PlaygroundAPI.newFeature = newFeature;
```

### Code Style Guidelines

#### Python Code Style
- **PEP 8 Compliance**: Follow Python style guidelines
- **Type Hints**: Use type hints for all function parameters and returns
- **Docstrings**: Google-style docstrings for all public methods
- **Error Handling**: Comprehensive error handling with appropriate exceptions

#### JavaScript Code Style
- **ES6+**: Use modern JavaScript features
- **JSDoc Comments**: Document all functions with JSDoc
- **Error Handling**: Proper try-catch blocks for async operations
- **Constants**: Use meaningful constant names in UPPER_CASE

#### CSS Code Style
- **BEM Methodology**: Use Block-Element-Modifier naming convention
- **OKLCH Colors**: Exclusively use OKLCH color space
- **Mobile-First**: Responsive design with mobile-first approach
- **Performance**: Optimize for performance with efficient selectors

## 🧪 Testing Guide

### Manual Testing Checklist

#### Validation Testing
- [ ] Load quick start examples
- [ ] Validate valid resources (should pass)
- [ ] Validate invalid resources (should show errors)
- [ ] Test verbose vs quick validation modes
- [ ] Verify keyboard shortcuts work
- [ ] Test error handling for malformed JSON

#### UI/UX Testing
- [ ] Navigation between pages works
- [ ] Responsive design on different screen sizes
- [ ] Hover effects and animations work
- [ ] Loading states display properly
- [ ] Notifications appear and dismiss correctly

#### API Testing
```bash
# Test validation endpoint
curl -X POST "http://localhost:5072/playground/api/validate" \
  -H "Content-Type: application/json" \
  -d '{"resource": {"resourceType": "Patient", "id": "test"}, "verbose": false}'

# Test examples endpoint
curl "http://localhost:5072/playground/api/examples/valid/patient"

# Test profiles endpoint  
curl "http://localhost:5072/playground/api/profiles"
```

### Automated Testing

Consider implementing:
- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test API endpoints and database interactions
- **E2E Tests**: Test complete user workflows
- **Performance Tests**: Validate response times and resource usage

## 🔒 Security Considerations

### Input Validation
- **JSON Validation**: All JSON inputs are validated before processing
- **Size Limits**: Large payloads are rejected to prevent DoS
- **XSS Prevention**: All user inputs are properly escaped
- **CSRF Protection**: Use CSRF tokens for form submissions

### API Security
- **Rate Limiting**: Implement rate limiting for API endpoints
- **Authentication**: Consider adding authentication for production use
- **CORS**: Properly configure CORS headers
- **HTTPS**: Always use HTTPS in production

## 📊 Performance Optimization

### Frontend Optimization
- **Asset Minification**: Minify CSS and JavaScript in production
- **Image Optimization**: Use appropriate image formats and sizes
- **Caching**: Implement browser caching for static assets
- **CDN**: Use CDN for external libraries like Lucide icons

### Backend Optimization
- **Response Caching**: Cache frequently requested data
- **Database Indexing**: Proper indexing for database queries
- **Async Operations**: Use async/await for I/O operations
- **Memory Management**: Efficient memory usage for large resources

## 🚀 Deployment Guide

### Production Checklist
- [ ] Set up proper environment variables
- [ ] Configure reverse proxy (nginx/Apache)
- [ ] Enable HTTPS with SSL certificates
- [ ] Set up monitoring and logging
- [ ] Configure backup strategies
- [ ] Implement health checks

### Docker Deployment
```dockerfile
# Example Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5072

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5072"]
```

## 🤝 Contributing

### Contributing Guidelines
1. **Fork the Repository**: Create your own fork
2. **Create Feature Branch**: Use descriptive branch names
3. **Follow Code Style**: Adhere to established style guidelines
4. **Add Tests**: Include tests for new functionality
5. **Update Documentation**: Keep documentation current
6. **Submit Pull Request**: Provide clear description of changes

### Issue Reporting
When reporting issues, include:
- **Environment Details**: OS, Python version, browser
- **Steps to Reproduce**: Clear, numbered steps
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Screenshots**: Visual evidence if applicable

## 📄 License

This project is part of the PHCore FHIR Validation Server and follows the same licensing terms. It is intended for healthcare interoperability in the Philippines and should be used in accordance with applicable healthcare data regulations.

## 🆘 Support

For support and questions:

1. **Documentation**: Check this README and the in-app documentation
2. **Examples**: Review the examples library for common patterns
3. **API Reference**: Use the built-in API documentation
4. **Community**: Engage with the PHCore development community

---

**Built with ❤️ for Philippine Healthcare Interoperability**
