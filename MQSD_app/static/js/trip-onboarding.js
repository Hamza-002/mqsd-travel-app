document.addEventListener('DOMContentLoaded', function() {
    const nextButton = document.getElementById('nextButton');
    
    // Handle option card clicks if they exist
    const optionCards = document.querySelectorAll('.option-card');
    if (optionCards.length > 0) {
        optionCards.forEach(card => {
            card.addEventListener('click', function() {
                // Remove active class from all cards
                optionCards.forEach(c => c.classList.remove('active'));
                // Add active class to clicked card
                this.classList.add('active');
                // Enable next button
                nextButton.disabled = false;
            });
        });
    }

    // Handle interest button clicks if they exist
    const interestButtons = document.querySelectorAll('.interest-btn:not(.add-interest)');
    if (interestButtons.length > 0) {
        interestButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Toggle active class
                this.classList.toggle('active');
                
                // Enable next button if at least one interest is selected
                const activeInterests = document.querySelectorAll('.interest-btn.active');
                nextButton.disabled = activeInterests.length === 0;
            });
        });
    }

    // Handle add interest button if it exists
    const addInterestButton = document.querySelector('.add-interest');
    if (addInterestButton) {
        addInterestButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Create input element
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'custom-interest-input';
            input.placeholder = 'Type and press Enter';
            
            // Replace button with input
            const parentDiv = this.parentElement;
            parentDiv.replaceChild(input, this);
            input.focus();

            // Handle input events
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && this.value.trim()) {
                    // Create new interest button
                    const newInterest = document.createElement('button');
                    newInterest.className = 'interest-btn';
                    newInterest.textContent = this.value.trim();
                    
                    // Add click handler to new button
                    newInterest.addEventListener('click', function() {
                        this.classList.toggle('active');
                        const activeInterests = document.querySelectorAll('.interest-btn.active');
                        nextButton.disabled = activeInterests.length === 0;
                    });

                    // Create new container for the interest
                    const newInterestOption = document.createElement('div');
                    newInterestOption.className = 'interest-option';
                    newInterestOption.appendChild(newInterest);

                    // Insert new interest before the add interest button
                    const interestsGrid = document.querySelector('.interests-grid');
                    interestsGrid.insertBefore(newInterestOption, parentDiv);

                    // Restore add interest button
                    parentDiv.replaceChild(addInterestButton, this);
                }
            });

            // Handle blur event
            input.addEventListener('blur', function() {
                // Restore add interest button if input is empty
                if (!this.value.trim()) {
                    parentDiv.replaceChild(addInterestButton, this);
                }
            });
        });
    }

    // Handle close button if it exists
    const closeButton = document.querySelector('.close-button');
    if (closeButton) {
        closeButton.addEventListener('click', function() {
            const warningModal = new bootstrap.Modal(document.getElementById('warningModal'));
            warningModal.show();
        });
    }

    // Handle confirm exit if it exists
    const confirmExitButton = document.getElementById('confirmExit');
    if (confirmExitButton) {
        confirmExitButton.addEventListener('click', function() {
            // Add exit functionality here
            console.log('Confirmed exit');
            window.location.href = 'index.html';
        });
    }

    // Handle next button click
    if (nextButton) {
        nextButton.addEventListener('click', function() {
            const currentPath = window.location.pathname;
            const currentPage = currentPath.split('/').pop();
            
            // Define page navigation
            const nextPageNavigation = {
                'trip-onboarding.html': 'trip-onboarding-2.html',
                'trip-onboarding-2.html': 'trip-onboarding-3.html',
                'trip-onboarding-3.html': 'trip-onboarding-4.html'
            };

            // Navigate to the next page
            const nextPage = nextPageNavigation[currentPage];
            if (nextPage) {
                window.location.href = nextPage;
            }
        });
    }

    // Handle back button navigation
    const backButton = document.querySelector('.btn-back');
    if (backButton) {
        backButton.addEventListener('click', function() {
            const currentPath = window.location.pathname;
            const currentPage = currentPath.split('/').pop();
            
            // Define page navigation for back button
            const previousPageNavigation = {
                'trip-onboarding-4.html': 'trip-onboarding-3.html',
                'trip-onboarding-3.html': 'trip-onboarding-2.html',
                'trip-onboarding-2.html': 'trip-onboarding.html'
            };

            // Navigate to the previous page
            const previousPage = previousPageNavigation[currentPage];
            if (previousPage) {
                window.location.href = previousPage;
            }
        });
    }

    // Initialize next button as disabled if no option is selected
    if (nextButton) {
        const selectedOption = document.querySelector('.option-card.selected') || 
                             document.querySelector('.option-card.active');
        nextButton.disabled = !selectedOption;
    }
}); 