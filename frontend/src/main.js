/**
 * Voice Agent Platform Frontend - Main JavaScript
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// API Utility Functions
class ApiClient {
    static async get(endpoint) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API GET Error:', error);
            throw error;
        }
    }

    static async post(endpoint, data) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API POST Error:', error);
            throw error;
        }
    }
}

// Status Checking Functions
async function checkApiStatus() {
    const statusElement = document.getElementById('api-status');
    try {
        const response = await ApiClient.get('/health');
        statusElement.textContent = response.status === 'healthy' ? 'Online' : 'Issues Detected';
        statusElement.className = 'status-indicator ' + (response.status === 'healthy' ? 'healthy' : 'unhealthy');
    } catch (error) {
        statusElement.textContent = 'Offline';
        statusElement.className = 'status-indicator unhealthy';
        console.error('API Health Check Failed:', error);
    }
}

async function checkDatabaseStatus() {
    const statusElement = document.getElementById('db-status');
    try {
        const response = await ApiClient.get('/health/db');
        statusElement.textContent = response.status === 'healthy' ? 'Connected' : 'Connection Issues';
        statusElement.className = 'status-indicator ' + (response.status === 'healthy' ? 'healthy' : 'unhealthy');
    } catch (error) {
        statusElement.textContent = 'Disconnected';
        statusElement.className = 'status-indicator unhealthy';
        console.error('Database Health Check Failed:', error);
    }
}

// Navigation Functions
function startOnboarding() {
    alert('Onboarding flow will be implemented in Phase 2');
    // TODO: Implement onboarding flow
}

function viewAgents() {
    alert('Agent listing will be implemented in Phase 2');
    // TODO: Implement agent listing
}

// Navigation Handler
function handleNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            // Add active class to clicked link
            e.target.classList.add('active');
            
            // Get the section from href
            const section = e.target.getAttribute('href').substring(1);
            
            // Handle navigation (placeholder for now)
            switch(section) {
                case 'agents':
                    console.log('Navigate to agents');
                    break;
                case 'onboarding':
                    console.log('Navigate to onboarding');
                    break;
                case 'analytics':
                    console.log('Navigate to analytics');
                    break;
            }
        });
    });
}

// App Initialization
async function initApp() {
    console.log('Voice Agent Platform Frontend Initialized');
    
    // Check system status once on startup
    await checkApiStatus();
    await checkDatabaseStatus();
    
    // Setup navigation
    handleNavigation();
    
    // Set up periodic status checks (every 5 minutes instead of 30 seconds)
    setInterval(async () => {
        await checkApiStatus();
        await checkDatabaseStatus();
    }, 300000); // 5 minutes = 300000ms
}

// Global Functions (for HTML onclick handlers)
window.startOnboarding = startOnboarding;
window.viewAgents = viewAgents;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initApp);
