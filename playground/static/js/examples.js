/**
 * PHCore FHIR Examples JavaScript
 * Functionality for the examples browser page
 */

// Global state for examples page
let currentModalData = null;
let currentFilters = {
    validity: 'all',
    resourceType: 'all'
};

/**
 * Filter examples by validity (all, valid, invalid)
 * @param {string} validity - Filter type
 */
function filterExamples(validity) {
    currentFilters.validity = validity;
    applyFilters();
    
    // Update active filter button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.filter === validity) {
            btn.classList.add('active');
        }
    });
}

/**
 * Filter examples by resource type
 */
function filterByResourceType() {
    const select = document.getElementById('resourceTypeFilter');
    currentFilters.resourceType = select.value;
    applyFilters();
}

/**
 * Apply current filters to the examples
 */
function applyFilters() {
    const sections = document.querySelectorAll('.examples-section');
    const groups = document.querySelectorAll('.resource-type-group');
    
    let hasVisibleItems = false;
    
    // Handle validity filter
    sections.forEach(section => {
        const sectionId = section.id;
        const isValid = sectionId === 'validSection';
        const isInvalid = sectionId === 'invalidSection';
        
        if (currentFilters.validity === 'all' || 
            (currentFilters.validity === 'valid' && isValid) ||
            (currentFilters.validity === 'invalid' && isInvalid)) {
            section.style.display = 'block';
        } else {
            section.style.display = 'none';
        }
    });
    
    // Handle resource type filter
    groups.forEach(group => {
        const resourceType = group.dataset.resourceType;
        const validity = group.dataset.validity;
        const parentSection = group.closest('.examples-section');
        
        // Check if parent section is visible
        const parentVisible = parentSection.style.display !== 'none';
        
        if (parentVisible && 
            (currentFilters.resourceType === 'all' || currentFilters.resourceType === resourceType)) {
            group.style.display = 'block';
            hasVisibleItems = true;
        } else {
            group.style.display = 'none';
        }
    });
    
    // Show/hide empty state
    showEmptyStateIfNeeded(hasVisibleItems);
}

/**
 * Show empty state if no examples match filters
 * @param {boolean} hasVisibleItems - Whether any items are visible
 */
function showEmptyStateIfNeeded(hasVisibleItems) {
    let emptyState = document.querySelector('.empty-state');
    
    if (!hasVisibleItems) {
        if (!emptyState) {
            emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.innerHTML = `
                <i data-lucide="search-x"></i>
                <h3>No Examples Found</h3>
                <p>No examples match your current filter criteria. Try adjusting your filters to see more results.</p>
            `;
            document.querySelector('.main-content').appendChild(emptyState);
            
            // Re-initialize icons
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }
        emptyState.style.display = 'block';
    } else {
        if (emptyState) {
            emptyState.style.display = 'none';
        }
    }
}

/**
 * View an example from button click (wrapper for data attributes)
 * @param {HTMLElement} button - Button element with data attributes
 */
function viewExampleFromButton(button) {
    try {
        const filename = button.dataset.filename;
        const dataJson = button.dataset.exampleData;
        const data = JSON.parse(dataJson);
        viewExample(filename, data);
    } catch (error) {
        console.error('Failed to parse example data:', error);
        showNotification('Failed to load example data', 'error');
    }
}

/**
 * View an example in a modal
 * @param {string} filename - Example filename
 * @param {Object} data - Example data
 */
function viewExample(filename, data) {
    currentModalData = data;
    
    const modal = document.getElementById('exampleModal');
    const title = document.getElementById('modalTitle');
    const content = document.getElementById('modalContent');
    
    title.textContent = filename;
    content.textContent = JSON.stringify(data, null, 2);
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    // Re-initialize icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

/**
 * Close the example modal
 */
function closeExampleModal() {
    const modal = document.getElementById('exampleModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    currentModalData = null;
}

/**
 * Validate an example from button click (wrapper for data attributes)
 * @param {HTMLElement} button - Button element with data attributes
 */
function validateExampleFromButton(button) {
    try {
        const filename = button.dataset.filename;
        const dataJson = button.dataset.exampleData;
        const data = JSON.parse(dataJson);
        validateExample(filename, data);
    } catch (error) {
        console.error('Failed to parse example data:', error);
        showNotification('Failed to load example data', 'error');
    }
}

/**
 * Validate an example (redirect to validator with data)
 * @param {string} filename - Example filename
 * @param {Object} data - Example data
 */
function validateExample(filename, data) {
    // Store the example data in sessionStorage
    sessionStorage.setItem('playgroundExample', JSON.stringify({
        filename: filename,
        data: data
    }));
    
    // Redirect to validator
    window.location.href = '/playground/validator';
}

/**
 * Validate from modal (current modal data)
 */
function validateFromModal() {
    if (currentModalData) {
        const title = document.getElementById('modalTitle').textContent;
        validateExample(title, currentModalData);
    }
}

/**
 * Copy example from button click (wrapper for data attributes)
 * @param {HTMLElement} button - Button element with data attributes
 */
function copyExampleFromButton(button) {
    try {
        const dataJson = button.dataset.exampleData;
        const data = JSON.parse(dataJson);
        copyExample(data);
    } catch (error) {
        console.error('Failed to parse example data:', error);
        showNotification('Failed to load example data', 'error');
    }
}

/**
 * Copy example to clipboard
 * @param {Object} data - Example data
 */
function copyExample(data) {
    const jsonString = JSON.stringify(data, null, 2);
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(jsonString).then(() => {
            showNotification('Example copied to clipboard', 'success');
        }).catch(err => {
            console.error('Failed to copy to clipboard:', err);
            fallbackCopyToClipboard(jsonString);
        });
    } else {
        fallbackCopyToClipboard(jsonString);
    }
}

/**
 * Fallback copy to clipboard for browsers without clipboard API
 * @param {string} text - Text to copy
 */
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showNotification('Example copied to clipboard', 'success');
    } catch (err) {
        console.error('Fallback copy failed:', err);
        showNotification('Failed to copy to clipboard', 'error');
    }
    
    document.body.removeChild(textArea);
}

/**
 * Show notification (reuse from main playground.js)
 * @param {string} message - Notification message
 * @param {string} type - Notification type
 */
function showNotification(message, type = 'info') {
    // Use the function from playground.js if available
    if (window.PlaygroundAPI && window.PlaygroundAPI.showNotification) {
        window.PlaygroundAPI.showNotification(message, type);
        return;
    }
    
    // Fallback implementation
    console.log(`${type.toUpperCase()}: ${message}`);
}

// Initialize examples page
document.addEventListener('DOMContentLoaded', function() {
    // Set up keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Escape: Close modal
        if (event.key === 'Escape') {
            closeExampleModal();
        }
    });
    
    // Initialize filters
    applyFilters();
    
    console.log('PHCore FHIR Examples page initialized');
});

// Handle browser back/forward buttons to close modal
window.addEventListener('popstate', function() {
    closeExampleModal();
});

// Export functions for global access
window.ExamplesAPI = {
    filterExamples,
    filterByResourceType,
    viewExample,
    viewExampleFromButton,
    validateExample,
    validateExampleFromButton,
    copyExample,
    copyExampleFromButton,
    closeExampleModal,
    validateFromModal
};
