// Admin panel JavaScript functionality

// Global variables
let originalFormData = {};
let currentMonitorToRename = '';
let currentMonitorToDelete = '';

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeForm();
    storeOriginalData();
});

// Store original form data for reset functionality
function storeOriginalData() {
    const form = document.getElementById('linksForm');
    const formData = new FormData(form);
    originalFormData = {};
    
    for (let [key, value] of formData.entries()) {
        originalFormData[key] = value;
    }
}

// Initialize form with validation
function initializeForm() {
    const form = document.getElementById('linksForm');
    const inputs = form.querySelectorAll('input[type="url"]');
    
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            validateUrlInput(this);
        });
        
        input.addEventListener('blur', function() {
            validateUrlInput(this);
        });
    });
    
    // Form submission validation
    form.addEventListener('submit', function(e) {
        if (!validateAllInputs()) {
            e.preventDefault();
            showToast('Sprawdź poprawność wszystkich URL-i przed zapisaniem', 'error');
        }
    });
}

// Validate individual URL input
function validateUrlInput(input) {
    const url = input.value.trim();
    const feedbackElement = document.getElementById(input.id + '_feedback');
    
    if (url === '') {
        input.classList.remove('is-valid', 'is-invalid');
        feedbackElement.textContent = '';
        return;
    }
    
    if (isValidUrl(url)) {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        feedbackElement.textContent = '';
    } else {
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
        feedbackElement.textContent = 'Nieprawidłowy format URL. Użyj http:// lub https://';
    }
}

// Validate all form inputs
function validateAllInputs() {
    const form = document.getElementById('linksForm');
    const inputs = form.querySelectorAll('input[type="url"]');
    let allValid = true;
    
    inputs.forEach(input => {
        validateUrlInput(input);
        if (input.classList.contains('is-invalid')) {
            allValid = false;
        }
    });
    
    return allValid;
}

// URL validation function
function isValidUrl(url) {
    try {
        const urlObj = new URL(url);
        return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch (e) {
        return false;
    }
}

// Validate URL via API
async function validateUrl(tvId) {
    const input = document.getElementById(tvId);
    const url = input.value.trim();
    
    if (!url) {
        showToast('Proszę wprowadzić URL', 'warning');
        return;
    }
    
    const button = input.parentElement.querySelector('.btn-outline-secondary');
    const originalIcon = button.innerHTML;
    
    // Show loading state
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    button.disabled = true;
    
    try {
        const response = await fetch('/api/validate_url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        const data = await response.json();
        
        if (data.valid) {
            showToast(`URL dla ${tvId} jest prawidłowy`, 'success');
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        } else {
            showToast(`Błąd walidacji dla ${tvId}: ${data.message}`, 'error');
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
        }
    } catch (error) {
        showToast('Błąd podczas walidacji URL', 'error');
        console.error('Validation error:', error);
    } finally {
        // Restore button state
        button.innerHTML = originalIcon;
        button.disabled = false;
    }
}

// Preview URL in modal
function previewUrl(url) {
    if (!url || url === 'https://www.example.com') {
        showToast('Brak prawidłowego URL do podglądu', 'warning');
        return;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    const iframe = document.getElementById('previewFrame');
    
    iframe.src = url;
    modal.show();
}

// Reset form to original values
function resetForm() {
    const form = document.getElementById('linksForm');
    const inputs = form.querySelectorAll('input[type="url"]');
    
    inputs.forEach(input => {
        input.value = originalFormData[input.name] || '';
        input.classList.remove('is-valid', 'is-invalid');
        
        const feedbackElement = document.getElementById(input.id + '_feedback');
        if (feedbackElement) {
            feedbackElement.textContent = '';
        }
    });
    
    showToast('Formularz został zresetowany', 'info');
}

// Refresh links from server
async function refreshLinks() {
    try {
        const response = await fetch('/api/links');
        const links = await response.json();
        
        // Update form with fresh data
        Object.keys(links).forEach(tvId => {
            const input = document.getElementById(tvId);
            if (input) {
                input.value = links[tvId];
                validateUrlInput(input);
            }
        });
        
        // Update stats
        document.getElementById('activeLinks').textContent = Object.keys(links).length;
        
        showToast('Linki zostały odświeżone', 'success');
    } catch (error) {
        showToast('Błąd podczas odświeżania linków', 'error');
        console.error('Refresh error:', error);
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    const toastId = 'toast-' + Date.now();
    
    const iconMap = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    const colorMap = {
        success: 'text-success',
        error: 'text-danger',
        warning: 'text-warning',
        info: 'text-info'
    };
    
    const toastHTML = `
        <div id="${toastId}" class="toast fade-in" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="${iconMap[type]} ${colorMap[type]} me-2"></i>
                <strong class="me-auto">Powiadomienie</strong>
                <small class="text-muted">teraz</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// Utility function to debounce rapid function calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Add debounced validation to inputs
document.addEventListener('DOMContentLoaded', function() {
    const inputs = document.querySelectorAll('input[type="url"]');
    inputs.forEach(input => {
        input.addEventListener('input', debounce(function() {
            validateUrlInput(this);
        }, 300));
    });
});

// Handle form changes detection
let formChanged = false;

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('linksForm');
    const inputs = form.querySelectorAll('input');
    
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            formChanged = true;
        });
    });
    
    // Warn user about unsaved changes
    window.addEventListener('beforeunload', function(e) {
        if (formChanged) {
            e.preventDefault();
            e.returnValue = 'Masz niezapisane zmiany. Czy na pewno chcesz opuścić stronę?';
        }
    });
    
    // Reset form change detection after successful save
    form.addEventListener('submit', function() {
        formChanged = false;
    });
});

// Monitor management functions

// Add new monitor
async function addMonitor() {
    const nameInput = document.getElementById('newMonitorName');
    const urlInput = document.getElementById('newMonitorUrl');
    const name = nameInput.value.trim();
    const url = urlInput.value.trim();
    
    // Clear previous validation
    nameInput.classList.remove('is-invalid');
    urlInput.classList.remove('is-invalid');
    
    if (!name) {
        nameInput.classList.add('is-invalid');
        document.getElementById('newMonitorName_feedback').textContent = 'Nazwa jest wymagana';
        return;
    }
    
    if (!isValidUrl(url)) {
        urlInput.classList.add('is-invalid');
        document.getElementById('newMonitorUrl_feedback').textContent = 'Nieprawidłowy format URL';
        return;
    }
    
    try {
        const response = await fetch('/add_monitor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: name, url: url })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('addMonitorModal')).hide();
            // Clear form
            nameInput.value = '';
            urlInput.value = 'https://www.example.com';
            // Refresh page to show new monitor
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Błąd podczas dodawania monitora', 'error');
        console.error('Add monitor error:', error);
    }
}

// Rename monitor
function renameMonitor(monitorName) {
    currentMonitorToRename = monitorName;
    document.getElementById('currentMonitorName').value = monitorName;
    document.getElementById('newMonitorNameEdit').value = monitorName;
    
    const modal = new bootstrap.Modal(document.getElementById('renameMonitorModal'));
    modal.show();
}

// Confirm rename
async function confirmRename() {
    const newNameInput = document.getElementById('newMonitorNameEdit');
    const newName = newNameInput.value.trim();
    
    // Clear previous validation
    newNameInput.classList.remove('is-invalid');
    
    if (!newName) {
        newNameInput.classList.add('is-invalid');
        document.getElementById('newMonitorNameEdit_feedback').textContent = 'Nowa nazwa jest wymagana';
        return;
    }
    
    if (newName === currentMonitorToRename) {
        newNameInput.classList.add('is-invalid');
        document.getElementById('newMonitorNameEdit_feedback').textContent = 'Nowa nazwa musi być różna od aktualnej';
        return;
    }
    
    try {
        const response = await fetch('/rename_monitor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                old_name: currentMonitorToRename, 
                new_name: newName 
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('renameMonitorModal')).hide();
            // Refresh page to show updated monitor name
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Błąd podczas zmiany nazwy monitora', 'error');
        console.error('Rename monitor error:', error);
    }
}

// Delete monitor
function deleteMonitor(monitorName) {
    currentMonitorToDelete = monitorName;
    document.getElementById('deleteMonitorName').textContent = monitorName;
    
    const modal = new bootstrap.Modal(document.getElementById('deleteMonitorModal'));
    modal.show();
}

// Confirm delete
async function confirmDelete() {
    try {
        const response = await fetch('/delete_monitor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: currentMonitorToDelete })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('deleteMonitorModal')).hide();
            // Remove monitor from DOM
            const monitorElement = document.getElementById('monitor-' + currentMonitorToDelete);
            if (monitorElement) {
                monitorElement.remove();
            }
            // Update stats
            await refreshLinks();
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Błąd podczas usuwania monitora', 'error');
        console.error('Delete monitor error:', error);
    }
}
