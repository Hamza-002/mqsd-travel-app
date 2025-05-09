// Function to check if user is authenticated (you'll need to implement this based on your authentication system)
function isUserAuthenticated() {
    // This is a placeholder - replace with your actual authentication check
    return false; // For testing purposes, always returning false
}

// Function to handle search button click
function handleSearch() {
    if (!isUserAuthenticated()) {
        // Show the login required modal
        const loginModal = new bootstrap.Modal(document.getElementById('loginRequiredModal'));
        loginModal.show();
    } else {
        // Proceed with search (implement your search logic here)
        document.querySelector('form').submit();
    }
}

// Function to restart the typing animation
function restartTypingAnimation() {
    const typingText = document.querySelector('.typing-text');
    typingText.style.animation = 'none';
    typingText.offsetHeight; // Trigger reflow
    typingText.style.animation = null;
}

// Initialize date range picker
function initializeDateRangePicker() {
    $('#dateRange').daterangepicker({
        autoUpdateInput: false,
        locale: {
            cancelLabel: 'Clear'
        }
    });

    $('#dateRange').on('apply.daterangepicker', function(ev, picker) {
        $(this).val(picker.startDate.format('MM/DD/YYYY') + ' - ' + picker.endDate.format('MM/DD/YYYY'));
        validateField(this);
    });

    $('#dateRange').on('cancel.daterangepicker', function(ev, picker) {
        $(this).val('');
        validateField(this);
    });
}

// Travelers dropdown functionality
document.addEventListener('DOMContentLoaded', function() {
    const travelersInput = document.getElementById('travelersInput');
    const travelersMenu = document.querySelector('.travelers-menu');
    
    // Counter elements
    const adultsCount = document.querySelector('.adults-count');
    const childrenCount = document.querySelector('.children-count');
    const decreaseAdults = document.querySelector('.decrease-adults');
    const increaseAdults = document.querySelector('.increase-adults');
    const decreaseChildren = document.querySelector('.decrease-children');
    const increaseChildren = document.querySelector('.increase-children');

    // Toggle dropdown
    travelersInput.addEventListener('click', function(e) {
        e.stopPropagation();
        travelersMenu.classList.toggle('show');
        updateInputValue();
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!travelersMenu.contains(e.target) && e.target !== travelersInput) {
            travelersMenu.classList.remove('show');
        }
    });

    // Handle counter buttons
    function updateCounter(type, action) {
        const countElement = type === 'adults' ? adultsCount : childrenCount;
        const decreaseBtn = type === 'adults' ? decreaseAdults : decreaseChildren;
        let count = parseInt(countElement.textContent);

        if (action === 'increase') {
            count++;
        } else if (action === 'decrease' && count > 0) {
            count--;
        }

        // Update counter display
        countElement.textContent = count;

        // Update decrease button state
        decreaseBtn.disabled = count === (type === 'adults' ? 1 : 0);

        // Update input value
        updateInputValue();
    }

    function updateInputValue() {
        const adults = parseInt(adultsCount.textContent);
        const children = parseInt(childrenCount.textContent);
        const adultsText = `${adults} Adult${adults !== 1 ? 's' : ''}`;
        const childrenText = children > 0 ? `, ${children} Child${children !== 1 ? 'ren' : ''}` : '';
        travelersInput.value = `${adultsText}${childrenText}`;
    }

    // Add click handlers for counter buttons
    increaseAdults.addEventListener('click', () => updateCounter('adults', 'increase'));
    decreaseAdults.addEventListener('click', () => updateCounter('adults', 'decrease'));
    increaseChildren.addEventListener('click', () => updateCounter('children', 'increase'));
    decreaseChildren.addEventListener('click', () => updateCounter('children', 'decrease'));

    // Initialize input value
    updateInputValue();
});

// Initialize all functionality when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Add event listener to search button
    const searchBtn = document.querySelector('.search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', handleSearch);
    }

    // Initialize date range picker
    initializeDateRangePicker();

    // Restart animation when clicking anywhere on the page
    document.addEventListener('click', restartTypingAnimation);

    // Restart animation periodically (every 10 seconds)
    setInterval(restartTypingAnimation, 10000);

    // Initialize travelers dropdown
    const travelersInput = document.getElementById('travelersInput');
    const adultsCount = document.querySelector('.adults-count');
    const childrenCount = document.querySelector('.children-count');
    const decreaseAdults = document.querySelector('.decrease-adults');
    const increaseAdults = document.querySelector('.increase-adults');
    const decreaseChildren = document.querySelector('.decrease-children');
    const increaseChildren = document.querySelector('.increase-children');

    let adults = 1;
    let children = 0;

    function updateTravelersInput() {
        const total = adults + children;
        travelersInput.value = `${total} Traveler${total > 1 ? 's' : ''}`;
        validateField(travelersInput);
    }

    updateTravelersInput();

    [decreaseAdults, increaseAdults, decreaseChildren, increaseChildren].forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            if (e.currentTarget.classList.contains('decrease-adults')) {
                if (adults > 1) adults--;
            } else if (e.currentTarget.classList.contains('increase-adults')) {
                if (adults < 10) adults++;
            } else if (e.currentTarget.classList.contains('decrease-children')) {
                if (children > 0) children--;
            } else if (e.currentTarget.classList.contains('increase-children')) {
                if (children < 10) children++;
            }
            
            adultsCount.textContent = adults;
            childrenCount.textContent = children;
            decreaseAdults.disabled = adults <= 1;
            decreaseChildren.disabled = children <= 0;
            increaseAdults.disabled = adults >= 10;
            increaseChildren.disabled = children >= 10;
            
            updateTravelersInput();
        });
    });

    // Search validation
    const searchButton = document.getElementById('searchButton');
    const citySelect = document.querySelector('.city-select');
    const searchValidationModal = new bootstrap.Modal(document.getElementById('searchValidationModal'));
    
    function validateField(field) {
        if (!field.value || field.value === 'Where are you Going?') {
            field.classList.add('is-invalid');
            return false;
        }
        field.classList.remove('is-invalid');
        return true;
    }

    function validateSearch() {
        const fields = [
            { element: citySelect, name: 'destination' },
            { element: document.getElementById('dateRange'), name: 'dates' },
            { element: document.getElementById('travelersInput'), name: 'travelers' }
        ];

        const missingFields = fields.filter(field => !validateField(field.element));
        
        if (missingFields.length > 0) {
            const missingFieldsList = document.querySelector('.missing-fields-list');
            missingFieldsList.innerHTML = missingFields
                .map(field => `<li>Please select ${field.name}</li>`)
                .join('');
            searchValidationModal.show();
            return false;
        }
        
        return true;
    }

    // Add validation on field change
    citySelect.addEventListener('change', () => validateField(citySelect));

    // Handle search button click
    searchButton.addEventListener('click', (e) => {
        e.preventDefault();
        if (validateSearch()) {
            window.location.href = 'trip-onboarding';
        }
    });
});
