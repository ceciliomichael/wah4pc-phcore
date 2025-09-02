/**
 * PHCore FHIR Playground JavaScript
 * Interactive functionality for the playground interface
 */

// Global state
let currentResource = null;
let validationInProgress = false;

// Initialize playground when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializePlayground();
});

/**
 * Initialize playground functionality
 */
function initializePlayground() {
    // Set up navigation active states
    updateActiveNavigation();
    
    // Set up keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Auto-resize textarea
    setupEditorAutoResize();
    
    console.log('PHCore FHIR Playground initialized');
}

/**
 * Update active navigation based on current page
 */
function updateActiveNavigation() {
    const currentPath = window.location.pathname;
    const navTabs = document.querySelectorAll('.nav-tab');
    
    navTabs.forEach(tab => {
        tab.classList.remove('active');
        if (tab.getAttribute('href') === currentPath) {
            tab.classList.add('active');
        }
    });
}

/**
 * Set up keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        // Ctrl/Cmd + Enter: Validate resource
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            event.preventDefault();
            validateResource();
        }
        
        // Ctrl/Cmd + K: Clear editor
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            clearEditor();
        }
        
        // Escape: Hide results
        if (event.key === 'Escape') {
            hideValidationResults();
        }
    });
}

/**
 * Set up auto-resize for textarea
 */
function setupEditorAutoResize() {
    const editor = document.getElementById('resourceEditor');
    if (editor) {
        editor.addEventListener('input', function() {
            // Auto-resize based on content
            this.style.height = 'auto';
            this.style.height = Math.max(300, this.scrollHeight) + 'px';
        });
    }
}

/**
 * Load a quick start example into the editor
 * @param {string} resourceType - Type of FHIR resource
 * @param {Object} resourceData - FHIR resource data
 */
function loadQuickExample(resourceType, resourceData) {
    const editor = document.getElementById('resourceEditor');
    if (!editor) {
        console.error('Resource editor not found');
        return;
    }
    
    // Pretty print JSON
    const formattedJson = JSON.stringify(resourceData, null, 2);
    editor.value = formattedJson;
    
    // Trigger auto-resize
    editor.style.height = 'auto';
    editor.style.height = Math.max(300, editor.scrollHeight) + 'px';
    
    // Scroll to editor
    document.getElementById('resourceEditor').scrollIntoView({ 
        behavior: 'smooth',
        block: 'center'
    });
    
    // Store current resource
    currentResource = resourceData;
    
    // Hide any existing results
    hideValidationResults();
    
    // Show success notification
    showNotification(`Loaded ${resourceType} example`, 'success');
}

/**
 * Clear the resource editor
 */
function clearEditor() {
    const editor = document.getElementById('resourceEditor');
    if (editor) {
        editor.value = '';
        editor.style.height = '300px';
        currentResource = null;
        hideValidationResults();
        showNotification('Editor cleared', 'info');
    }
}

/**
 * Validate the current resource in the editor
 */
async function validateResource() {
    if (validationInProgress) {
        console.log('Validation already in progress');
        return;
    }
    
    const editor = document.getElementById('resourceEditor');
    const verboseCheckbox = document.getElementById('verboseMode');
    
    if (!editor || !editor.value.trim()) {
        showNotification('Please enter a FHIR resource to validate', 'warning');
        return;
    }
    
    // Parse JSON
    let resourceData;
    try {
        resourceData = JSON.parse(editor.value);
    } catch (error) {
        showValidationResults({
            success: false,
            issues: [{
                severity: 'error',
                code: 'invalid',
                details: `JSON parsing error: ${error.message}`,
                location: 'root',
                severity_class: 'error'
            }],
            total_issues: 1,
            error_count: 1,
            warning_count: 0
        });
        return;
    }
    
    // Show loading
    showLoading();
    validationInProgress = true;
    
    try {
        const response = await fetch('/playground/api/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                resource: resourceData,
                verbose: verboseCheckbox ? verboseCheckbox.checked : true
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showValidationResults(result);
        } else {
            throw new Error(result.error || 'Validation failed');
        }
        
    } catch (error) {
        console.error('Validation error:', error);
        showValidationResults({
            success: false,
            issues: [{
                severity: 'error',
                code: 'exception',
                details: `Validation error: ${error.message}`,
                location: 'root',
                severity_class: 'error'
            }],
            total_issues: 1,
            error_count: 1,
            warning_count: 0
        });
    } finally {
        hideLoading();
        validationInProgress = false;
    }
}

/**
 * Show validation results
 * @param {Object} result - Validation result object
 */
function showValidationResults(result) {
    const resultsContainer = document.getElementById('validationResults');
    const summaryContainer = document.getElementById('resultsSummary');
    const contentContainer = document.getElementById('resultsContent');
    
    if (!resultsContainer || !summaryContainer || !contentContainer) {
        console.error('Validation results containers not found');
        return;
    }
    
    // Clear previous content
    summaryContainer.innerHTML = '';
    contentContainer.innerHTML = '';
    
    // Create summary
    const summaryHtml = createResultsSummary(result);
    summaryContainer.innerHTML = summaryHtml;
    
    // Create issues list
    const issuesHtml = createIssuesList(result.issues || []);
    contentContainer.innerHTML = issuesHtml;
    
    // Show results
    resultsContainer.style.display = 'block';
    
    // Scroll to results
    resultsContainer.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
    });
    
    // Re-initialize icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

/**
 * Create results summary HTML
 * @param {Object} result - Validation result
 * @returns {string} HTML string
 */
function createResultsSummary(result) {
    const statusClass = result.success ? 'success' : 'error';
    const statusText = result.success ? 'Valid' : 'Invalid';
    const statusIcon = result.success ? 'check-circle' : 'x-circle';
    
    let html = `
        <div class="result-badge ${statusClass}">
            <i data-lucide="${statusIcon}"></i>
            ${statusText}
        </div>
    `;
    
    if (result.total_issues > 0) {
        if (result.error_count > 0) {
            html += `
                <div class="result-badge error">
                    <i data-lucide="alert-circle"></i>
                    ${result.error_count} Error${result.error_count !== 1 ? 's' : ''}
                </div>
            `;
        }
        
        if (result.warning_count > 0) {
            html += `
                <div class="result-badge warning">
                    <i data-lucide="alert-triangle"></i>
                    ${result.warning_count} Warning${result.warning_count !== 1 ? 's' : ''}
                </div>
            `;
        }
    }
    
    return html;
}

/**
 * Create issues list HTML
 * @param {Array} issues - Array of validation issues
 * @returns {string} HTML string
 */
function createIssuesList(issues) {
    if (!issues || issues.length === 0) {
        return `
            <div class="issue-item info">
                <div class="issue-header">
                    <div class="issue-severity info">
                        <i data-lucide="check-circle"></i>
                        Success
                    </div>
                    <div class="issue-title">Validation Successful</div>
                </div>
                <div class="issue-details">
                    Resource validation completed successfully. No issues found.
                </div>
            </div>
        `;
    }
    
    return issues.map(issue => {
        const severityIcon = getSeverityIcon(issue.severity);
        const severityLabel = issue.severity.charAt(0).toUpperCase() + issue.severity.slice(1);
        return `
            <div class="issue-item ${issue.severity_class}">
                <div class="issue-header">
                    <div class="issue-severity ${issue.severity_class}">
                        <i data-lucide="${severityIcon}"></i>
                        ${severityLabel}
                    </div>
                    <div class="issue-title">Validation Issue</div>
                </div>
                <div class="issue-details">
                    ${escapeHtml(issue.details)}
                    <div class="issue-location">
                        <i data-lucide="map-pin"></i>
                        Location: ${escapeHtml(issue.location)}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Get icon for severity level
 * @param {string} severity - Severity level
 * @returns {string} Icon name
 */
function getSeverityIcon(severity) {
    const iconMap = {
        'error': 'x-circle',
        'warning': 'alert-triangle',
        'information': 'info',
        'fatal': 'x-octagon'
    };
    return iconMap[severity] || 'info';
}

/**
 * Hide validation results
 */
function hideValidationResults() {
    const resultsContainer = document.getElementById('validationResults');
    if (resultsContainer) {
        resultsContainer.style.display = 'none';
    }
}

/**
 * Show loading overlay
 */
function showLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
    }
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

/**
 * Show notification message
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, warning, info)
 */
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notif => notif.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i data-lucide="${getNotificationIcon(type)}"></i>
            <span>${escapeHtml(message)}</span>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 2rem;
        right: 2rem;
        background: oklch(100% 0 0);
        border: 1px solid oklch(90% 0.01 210);
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 4px 12px oklch(0% 0 0 / 0.15);
        z-index: 1001;
        max-width: 400px;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
    `;
    
    // Add type-specific styling
    const typeColors = {
        success: 'oklch(30% 0.15 130)',
        error: 'oklch(40% 0.15 15)',
        warning: 'oklch(35% 0.15 60)',
        info: 'oklch(65% 0.15 220)'
    };
    
    notification.style.borderLeftColor = typeColors[type] || typeColors.info;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Initialize icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Animate in
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

/**
 * Get icon for notification type
 * @param {string} type - Notification type
 * @returns {string} Icon name
 */
function getNotificationIcon(type) {
    const iconMap = {
        success: 'check-circle',
        error: 'x-circle',
        warning: 'alert-triangle',
        info: 'info'
    };
    return iconMap[type] || 'info';
}

/**
 * Escape HTML entities
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Copied to clipboard', 'success');
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        showNotification('Failed to copy to clipboard', 'error');
    }
}

/**
 * Download text as file
 * @param {string} content - File content
 * @param {string} filename - Filename
 * @param {string} contentType - MIME type
 */
function downloadFile(content, filename, contentType = 'application/json') {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
    showNotification(`Downloaded ${filename}`, 'success');
}

/**
 * Format JSON string
 * @param {string} jsonString - JSON string to format
 * @returns {string} Formatted JSON string
 */
function formatJson(jsonString) {
    try {
        const parsed = JSON.parse(jsonString);
        return JSON.stringify(parsed, null, 2);
    } catch (error) {
        return jsonString;
    }
}

// Export functions for global access
window.PlaygroundAPI = {
    loadQuickExample,
    validateResource,
    clearEditor,
    showNotification,
    copyToClipboard,
    downloadFile,
    formatJson
};
