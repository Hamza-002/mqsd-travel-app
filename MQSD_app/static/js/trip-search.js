// Initialize Google Map
function initMap() {
    // Example coordinates for Jazan, Saudi Arabia
    const jazan = { lat: 16.8892, lng: 42.5611 };
    
    const map = new google.maps.Map(document.getElementById('map'), {
        zoom: 13,
        center: jazan,
        styles: [
            {
                featureType: 'all',
                elementType: 'geometry',
                stylers: [{ color: '#f5f5f5' }]
            },
            {
                featureType: 'water',
                elementType: 'geometry',
                stylers: [{ color: '#c9e9e7' }]
            },
            {
                featureType: 'poi',
                elementType: 'geometry',
                stylers: [{ color: '#e8e8e8' }]
            }
        ]
    });

    // Add markers for trip locations
    const tripLocations = [
        {
            position: jazan,
            title: 'Jazan Town'
        }
        // Add more locations as needed
    ];

    tripLocations.forEach(location => {
        new google.maps.Marker({
            position: location.position,
            map: map,
            title: location.title,
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                scale: 8,
                fillColor: '#14AE5C',
                fillOpacity: 1,
                strokeColor: '#ffffff',
                strokeWeight: 2
            }
        });
    });
}

// Date Slider Functionality
document.addEventListener('DOMContentLoaded', function() {
    const dateItems = document.querySelectorAll('.date-item');
    
    dateItems.forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all items
            dateItems.forEach(di => di.classList.remove('active'));
            // Add active class to clicked item
            this.classList.add('active');
            
            // Here you would typically fetch and update the trip items for the selected date
            updateTripItems(this.querySelector('.date').textContent);
        });
    });
});

// Function to update trip items based on selected date
function updateTripItems(date) {
    // This is where you would make an API call to get trip items for the selected date
    console.log(`Fetching trips for date: ${date}`);
    // For now, we'll just log the date
}

// Search Functionality
const searchInput = document.querySelector('.search-input');
const searchButton = document.querySelector('.search-button');

searchButton.addEventListener('click', function() {
    performSearch(searchInput.value);
});

searchInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        performSearch(this.value);
    }
});

function performSearch(query) {
    // This is where you would implement the search functionality
    console.log(`Searching for: ${query}`);
}

// Profile Button Functionality
const profileButton = document.querySelector('.profile-image');
profileButton.addEventListener('click', function() {
    // Implement profile menu toggle
    console.log('Profile clicked');
});

// Edit Profile Button Functionality
const editProfileButton = document.querySelector('.edit-profile');
editProfileButton.addEventListener('click', function() {
    // Implement edit profile functionality
    console.log('Edit profile clicked');
}); 