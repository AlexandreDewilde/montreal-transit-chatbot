// Geolocation component for MTL Finder
// Automatically requests user location and sends it back to Streamlit

function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                // Send location data back to Streamlit
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        timestamp: position.timestamp
                    }
                }, '*');
            },
            function(error) {
                // Send error back to Streamlit
                let errorMessage = '';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'User denied the request for Geolocation.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Location information is unavailable.';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'The request to get user location timed out.';
                        break;
                    default:
                        errorMessage = 'An unknown error occurred.';
                        break;
                }

                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: {
                        error: errorMessage,
                        code: error.code
                    }
                }, '*');
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    } else {
        // Geolocation not supported
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: {
                error: 'Geolocation is not supported by this browser.'
            }
        }, '*');
    }
}

// Request location automatically on load
getLocation();
