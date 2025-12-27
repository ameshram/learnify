/**
 * Learnify - Main JavaScript
 *
 * This file handles:
 * - Theme toggling (light/dark mode)
 * - System preference detection
 * - Header scroll effects
 * - Toast notifications
 * - Global utilities
 */

// ==========================================================================
// THEME MANAGEMENT
// ==========================================================================

/**
 * Theme Toggle System
 *
 * How it works:
 * 1. On page load, check localStorage for saved preference
 * 2. If no preference, check system preference (prefers-color-scheme)
 * 3. Apply the theme by setting data-theme attribute on <html>
 * 4. Save preference to localStorage when user toggles
 *
 * The CSS uses [data-theme="dark"] selector to override light mode variables
 */

const ThemeManager = {
    STORAGE_KEY: 'learnify-theme',

    init() {
        // Get saved theme or detect system preference
        const savedTheme = localStorage.getItem(this.STORAGE_KEY);
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme = savedTheme || (systemPrefersDark ? 'dark' : 'light');

        // Apply theme
        this.setTheme(theme);

        // Setup toggle button
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggle());
        }

        // Listen for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem(this.STORAGE_KEY)) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    },

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(this.STORAGE_KEY, theme);
    },

    toggle() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        this.setTheme(next);
    },

    getTheme() {
        return document.documentElement.getAttribute('data-theme');
    }
};

// ==========================================================================
// HEADER SCROLL EFFECT
// ==========================================================================

/**
 * Adds glass effect to header on scroll
 */
const HeaderManager = {
    init() {
        const header = document.getElementById('header');
        if (!header) return;

        let lastScroll = 0;

        window.addEventListener('scroll', () => {
            const currentScroll = window.scrollY;

            if (currentScroll > 10) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }

            lastScroll = currentScroll;
        }, { passive: true });
    }
};

// ==========================================================================
// TOAST NOTIFICATIONS
// ==========================================================================

/**
 * Toast notification system
 *
 * Usage:
 * Toast.show('Message', 'success'); // or 'error', 'info'
 */
const Toast = {
    container: null,

    init() {
        this.container = document.getElementById('toast-container');
    },

    show(message, type = 'info', duration = 4000) {
        if (!this.container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const icons = {
            success: 'check-circle',
            error: 'x-circle',
            info: 'info'
        };

        toast.innerHTML = `
            <span class="toast-icon">
                <i data-lucide="${icons[type] || 'info'}" style="width: 20px; height: 20px;"></i>
            </span>
            <span class="toast-message">${message}</span>
        `;

        this.container.appendChild(toast);

        // Initialize icon
        if (window.lucide) {
            lucide.createIcons();
        }

        // Auto remove
        setTimeout(() => {
            toast.style.animation = 'slideUp 0.3s ease reverse forwards';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    success(message) {
        this.show(message, 'success');
    },

    error(message) {
        this.show(message, 'error');
    },

    info(message) {
        this.show(message, 'info');
    }
};

// ==========================================================================
// UTILITIES
// ==========================================================================

/**
 * Debounce function for performance
 */
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

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Animate element into view
 */
function animateIn(element, animation = 'animate-fade-in') {
    element.classList.add(animation);
}

// ==========================================================================
// INITIALIZATION
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
    HeaderManager.init();
    Toast.init();
});

// Make Toast available globally
window.Toast = Toast;
window.formatDate = formatDate;
