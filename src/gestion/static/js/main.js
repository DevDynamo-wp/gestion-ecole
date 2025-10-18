// ========== CONFIGURATION GLOBALE ==========
const SchoolPro = {
    debug: true,
    apiBase: '/api/',
    
    log: function(msg, type = 'info') {
        if (this.debug) {
            console.log(`[SchoolPro ${type.toUpperCase()}]`, msg);
        }
    }
};

// ========== MOBILE MENU ==========
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.querySelector('.sidebar');
    
    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            SchoolPro.log('Mobile menu toggled');
        });
        
        // Fermer le menu au clic en dehors
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.sidebar') && !e.target.closest('#mobile-menu-btn')) {
                sidebar.classList.remove('active');
            }
        });
    }
});

// ========== NAVIGATION ACTIVE ==========
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-item, .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.includes(href)) {
            link.classList.add('active');
            SchoolPro.log(`Active link set: ${href}`);
        }
    });
});

// ========== MODAL MANAGEMENT ==========
const Modal = {
    open: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
            SchoolPro.log(`Modal opened: ${modalId}`);
        }
    },
    
    close: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
            SchoolPro.log(`Modal closed: ${modalId}`);
        }
    },
    
    closeAll: function() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('show');
            modal.style.display = 'none';
        });
        document.body.style.overflow = 'auto';
    }
};

// Fermer modal au clic sur le fond
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('show');
        e.target.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
});

// Fermer modal avec touche Échap
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        Modal.closeAll();
    }
});

// ========== FORM VALIDATION ==========
const FormValidator = {
    validateEmail: function(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    },
    
    validatePhone: function(phone) {
        const regex = /^[\d\s\-\+\(\)]+$/;
        return regex.test(phone) && phone.replace(/\D/g, '').length >= 10;
    },
    
    validateForm: function(formId) {
        const form = document.getElementById(formId);
        if (!form) return false;
        
        const inputs = form.querySelectorAll('[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('border-red-500');
                isValid = false;
            } else {
                input.classList.remove('border-red-500');
            }
        });
        
        SchoolPro.log(`Form validation: ${isValid ? 'passed' : 'failed'}`);
        return isValid;
    }
};

// ========== TABLE INTERACTIONS ==========
const Table = {
    makeSelectable: function(tableSelector) {
        const table = document.querySelector(tableSelector);
        if (!table) return;
        
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.addEventListener('click', function() {
                this.classList.toggle('bg-blue-100');
            });
        });
        
        SchoolPro.log(`Table made selectable: ${tableSelector}`);
    },
    
    sortTable: function(tableSelector, columnIndex) {
        const table = document.querySelector(tableSelector);
        if (!table) return;
        
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        rows.sort((a, b) => {
            const aVal = a.children[columnIndex].textContent.trim();
            const bVal = b.children[columnIndex].textContent.trim();
            return aVal.localeCompare(bVal);
        });
        
        rows.forEach(row => tbody.appendChild(row));
        SchoolPro.log(`Table sorted by column ${columnIndex}`);
    },
    
    filterTable: function(tableSelector, searchText) {
        const table = document.querySelector(tableSelector);
        if (!table) return;
        
        const rows = table.querySelectorAll('tbody tr');
        let visibleCount = 0;
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchText.toLowerCase())) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });
        
        SchoolPro.log(`Table filtered. Visible rows: ${visibleCount}`);
    }
};

// ========== SEARCH DYNAMIQUE ==========
const DynamicSearch = {
    init: function(inputSelector, tableSelector) {
        const input = document.querySelector(inputSelector);
        if (!input) return;
        
        input.addEventListener('keyup', (e) => {
            const searchText = e.target.value;
            Table.filterTable(tableSelector, searchText);
        });
        
        SchoolPro.log(`Dynamic search initialized: ${inputSelector}`);
    }
};

// ========== NOTIFICATIONS ==========
const Notification = {
    show: function(message, type = 'info', duration = 5000) {
        const alertClass = {
            success: 'alert-success',
            error: 'alert-danger',
            warning: 'alert-warning',
            info: 'alert-info'
        }[type] || 'alert-info';
        
        const alertHTML = `
            <div class="alert ${alertClass} animate-slide-in-down">
                <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
                <span>${message}</span>
            </div>
        `;
        
        const container = document.querySelector('main') || document.body;
        const alertDiv = document.createElement('div');
        alertDiv.innerHTML = alertHTML;
        container.insertBefore(alertDiv.firstElementChild, container.firstChild);
        
        SchoolPro.log(`Notification shown: ${message}`, type);
        
        if (duration > 0) {
            setTimeout(() => {
                alertDiv.firstElementChild.remove();
            }, duration);
        }
    },
    
    success: function(msg) { this.show(msg, 'success'); },
    error: function(msg) { this.show(msg, 'error', 7000); },
    warning: function(msg) { this.show(msg, 'warning'); },
    info: function(msg) { this.show(msg, 'info'); }
};

// ========== API REQUESTS ==========
const API = {
    async get(endpoint) {
        try {
            const response = await fetch(SchoolPro.apiBase + endpoint);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            SchoolPro.log(`API GET error: ${error.message}`, 'error');
            throw error;
        }
    },
    
    async post(endpoint, data) {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
            const response = await fetch(SchoolPro.apiBase + endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            SchoolPro.log(`API POST error: ${error.message}`, 'error');
            throw error;
        }
    },
    
    async delete(endpoint) {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
            const response = await fetch(SchoolPro.apiBase + endpoint, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            SchoolPro.log(`API DELETE error: ${error.message}`, 'error');
            throw error;
        }
    }
};

// ========== DARK MODE TOGGLE ==========
const DarkMode = {
    init: function() {
        const isDark = localStorage.getItem('darkMode') === 'true';
        if (isDark) this.enable();
    },
    
    enable: function() {
        document.documentElement.classList.add('dark');
        localStorage.setItem('darkMode', 'true');
        SchoolPro.log('Dark mode enabled');
    },
    
    disable: function() {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('darkMode', 'false');
        SchoolPro.log('Dark mode disabled');
    },
    
    toggle: function() {
        if (document.documentElement.classList.contains('dark')) {
            this.disable();
        } else {
            this.enable();
        }
    }
};

// ========== UTILITY FUNCTIONS ==========
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('fr-FR', options);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR'
    }).format(amount);
}

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

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', function() {
    SchoolPro.log('SchoolPro initialized');
    DarkMode.init();
    
    // Auto-hide alerts after 5 secondes
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => alert.remove(), 5000);
    });
});

// ========== EXPORT FOR USAGE ==========
window.SchoolPro = SchoolPro;
window.Modal = Modal;
window.Notification = Notification;
window.Table = Table;
window.DynamicSearch = DynamicSearch;
window.API = API;
window.DarkMode = DarkMode;
window.formatDate = formatDate;
window.formatCurrency = formatCurrency;
window.debounce = debounce;