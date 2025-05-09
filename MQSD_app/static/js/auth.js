// Authentication functions
function isUserAuthenticated() {
    // This should be replaced with actual authentication check
    return false;
}

function handleSearch() {
    if (!isUserAuthenticated()) {
        const loginModal = new bootstrap.Modal(document.getElementById('loginRequiredModal'));
        loginModal.show();
    } else {
        document.querySelector('form').submit();
    }
}

// Slideshow functionality
function initSlideshow() {
    const slides = document.querySelectorAll('.slide');
    if (slides.length === 0) return; // Exit if no slides found
    
    let currentSlide = 0;
    
    function showNextSlide() {
        // Remove active class from current slide
        slides[currentSlide].classList.remove('active');
        
        // Move to next slide
        currentSlide = (currentSlide + 1) % slides.length;
        
        // Add active class to next slide
        slides[currentSlide].classList.add('active');
    }

    // Change slide every 5 seconds
    setInterval(showNextSlide, 2000);
}

// Initialize auth-related event listeners
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing slideshow...'); // Debug log
    initSlideshow();

    const searchBtn = document.querySelector('.search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', handleSearch);
    }

    // Handle login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        initLoginForm(loginForm);
    }

    // Handle signup form
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        initSignupForm(signupForm);
    }
});

function initLoginForm(loginForm) {
    const emailInput = loginForm.querySelector('#email');
    const passwordInput = loginForm.querySelector('#password');
    const submitButton = loginForm.querySelector('button[type="submit"]');

    // Initially disable the button
    submitButton.disabled = true;

    // Function to check if both fields are filled
    function checkFields() {
        const isEmailFilled = emailInput.value.trim() !== '';
        const isPasswordFilled = passwordInput.value.trim() !== '';
        submitButton.disabled = !(isEmailFilled && isPasswordFilled);
    }

    // Add input event listeners to both fields
    emailInput.addEventListener('input', checkFields);
    passwordInput.addEventListener('input', checkFields);

    // Handle form submission
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        if (!submitButton.disabled) {
            console.log('Login form submitted:', {
                email: emailInput.value,
                password: passwordInput.value
            });
        }
    });
}

function initSignupForm(signupForm) {
    const nameInput = signupForm.querySelector('#name');
    const usernameInput = signupForm.querySelector('#username');
    const emailInput = signupForm.querySelector('#email');
    const passwordInput = signupForm.querySelector('#password');
    const submitButton = signupForm.querySelector('button[type="submit"]');
    const inputs = [nameInput, usernameInput, emailInput, passwordInput];
    let formSubmitted = false;

    // Function to validate a single input
    function validateInput(input, showErrors = false) {
        if (!showErrors) {
            input.classList.remove('is-invalid', 'is-valid');
            return true;
        }

        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
            return false;
        } else {
            if (input === emailInput && !isValidEmail(input.value)) {
                input.classList.add('is-invalid');
                input.classList.remove('is-valid');
                return false;
            }
            if (input === passwordInput && input.value.length < 8) {
                input.classList.add('is-invalid');
                input.classList.remove('is-valid');
                return false;
            }
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            return true;
        }
    }

    // Function to validate email format
    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    // Function to validate all fields
    function validateForm() {
        let isValid = true;
        inputs.forEach(input => {
            if (!validateInput(input, true)) {
                isValid = false;
            }
        });
        return isValid;
    }

    // Add input event listeners to all fields
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            if (formSubmitted) {
                validateInput(input, true);
            }
        });

        input.addEventListener('blur', () => {
            if (input.value.trim() || formSubmitted) {
                validateInput(input, true);
            }
        });

        // Remove validation styles when user starts typing
        input.addEventListener('focus', () => {
            if (!formSubmitted) {
                input.classList.remove('is-invalid', 'is-valid');
            }
        });
    });

    // Handle form submission
    signupForm.addEventListener('submit', function(e) {
        e.preventDefault();
        formSubmitted = true;
        
        if (validateForm()) {
            console.log('Signup form submitted:', {
                name: nameInput.value,
                username: usernameInput.value,
                email: emailInput.value,
                password: passwordInput.value
            });
        }
    });
}

// Password toggle functionality
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const toggleButton = document.querySelector('.password-toggle i');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleButton.classList.remove('fa-eye');
        toggleButton.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        toggleButton.classList.remove('fa-eye-slash');
        toggleButton.classList.add('fa-eye');
    }
}