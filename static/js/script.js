// Audio player functionality
class AudioPlayer {
    constructor() {
        this.audioElements = document.querySelectorAll('audio');
        this.init();
    }

    init() {
        this.audioElements.forEach(audio => {
            audio.addEventListener('play', (e) => {
                // Pause other audio elements when one starts playing
                this.pauseOtherAudios(e.target);
            });
        });
    }

    pauseOtherAudios(currentAudio) {
        this.audioElements.forEach(audio => {
            if (audio !== currentAudio && !audio.paused) {
                audio.pause();
                audio.currentTime = 0;
            }
        });
    }
}

// Search functionality
class SearchManager {
    constructor() {
        this.searchInput = document.querySelector('.nav-search input');
        this.init();
    }

    init() {
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
        }
    }

    handleSearch(e) {
        const query = e.target.value;
        // Implement live search or redirect to search page
        if (query.length > 2) {
            // You can implement AJAX search here
            console.log('Searching for:', query);
        }
    }

    debounce(func, wait) {
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
}

// Form validation
class FormValidator {
    constructor() {
        this.forms = document.querySelectorAll('form');
        this.init();
    }

    init() {
        this.forms.forEach(form => {
            form.addEventListener('submit', this.validateForm.bind(this));
        });
    }

    validateForm(e) {
        const form = e.target;
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                this.showError(field, 'This field is required');
            } else {
                this.clearError(field);
            }

            // Email validation
            if (field.type === 'email' && field.value) {
                if (!this.isValidEmail(field.value)) {
                    isValid = false;
                    this.showError(field, 'Please enter a valid email');
                }
            }

            // Price validation
            if (field.name === 'price' && field.value) {
                if (parseFloat(field.value) <= 0) {
                    isValid = false;
                    this.showError(field, 'Price must be greater than 0');
                }
            }
        });

        if (!isValid) {
            e.preventDefault();
        }
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    showError(field, message) {
        this.clearError(field);
        field.style.borderColor = '#ff6b6b';
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.color = '#ff6b6b';
        errorDiv.style.fontSize = '0.8rem';
        errorDiv.style.marginTop = '0.5rem';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    clearError(field) {
        field.style.borderColor = '';
        const existingError = field.parentNode.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new AudioPlayer();
    new SearchManager();
    new FormValidator();

    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading states to buttons
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                submitBtn.disabled = true;
            }
        });
    });
});