// Import global styles
import './styles/main.css';

/**
 * Voice Agent Platform Frontend - Enhanced JavaScript
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// Global State
let currentSession = null;
let currentStep = 1;
let totalSteps = 6; // Updated from 3 to 6 steps
let uploadedFiles = [];
let questionCount = 0;
let selectedVoice = 'alloy';
let availableVoices = [];
let availableTools = [];
let selectedTools = [];

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

    static async put(endpoint, data) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'PUT',
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
            console.error('API PUT Error:', error);
            throw error;
        }
    }

    static async delete(endpoint) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'DELETE'
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API DELETE Error:', error);
            throw error;
        }
    }

    static async postFormData(endpoint, formData) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                body: formData
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API Form POST Error:', error);
            throw error;
        }
    }
}

// Page Navigation Functions
function showLanding() {
    hideAllPages();
    document.getElementById('landing-page').classList.remove('hidden');
    document.getElementById('landing-page').classList.add('fade-in');
}

function showCreateAgent() {
    hideAllPages();
    document.getElementById('onboarding-page').classList.remove('hidden');
    document.getElementById('onboarding-page').classList.add('fade-in');
    resetOnboarding();
}

function showDashboard() {
    // Redirect to standalone dashboard
    window.location.href = 'dashboard.html';
}

function hideAllPages() {
    const pages = ['landing-page', 'onboarding-page', 'dashboard-page'];
    pages.forEach(pageId => {
        const page = document.getElementById(pageId);
        page.classList.add('hidden');
        page.classList.remove('fade-in');
    });
}

function goBack() {
    if (currentStep === 1) {
        showLanding();
    } else {
        // Handle going back in onboarding steps
        currentStep--;
        updateProgress();
        showCurrentStep();
    }
}

// Onboarding Functions
function resetOnboarding() {
    currentStep = 1;
    currentSession = null;
    uploadedFiles = [];
    questionCount = 0;
    updateProgress();
    showCurrentStep();
    resetForms();
}

function updateProgress() {
    const progressFill = document.getElementById('progress-fill');
    const currentStepEl = document.getElementById('current-step');
    const totalStepsEl = document.getElementById('total-steps');
    
    const progress = (currentStep / totalSteps) * 100;
    progressFill.style.width = `${progress}%`;
    currentStepEl.textContent = currentStep;
    totalStepsEl.textContent = totalSteps;
}

function showCurrentStep() {
    // Hide all steps
    const steps = document.querySelectorAll('.onboarding-step');
    steps.forEach(step => step.classList.remove('active'));
    
    // Show current step
    let stepId;
    switch(currentStep) {
        case 1:
            stepId = 'step-data-upload';
            break;
        case 2:
            stepId = 'step-identity';
            break;
        case 3:
            stepId = 'step-voice';
            break;
        case 4:
            stepId = 'step-tools';
            break;
        case 5:
            stepId = 'step-interview';
            break;
        case 6:
            stepId = 'step-completion';
            break;
    }
    
    const currentStepEl = document.getElementById(stepId);
    if (currentStepEl) {
        currentStepEl.classList.add('active');
        currentStepEl.classList.add('fade-in');
    }
}

function resetForms() {
    document.getElementById('website-url').value = '';
    document.getElementById('pdf-upload').value = '';
    document.getElementById('uploaded-files').innerHTML = '';
    document.getElementById('start-processing-btn').disabled = true;
}

// File Upload Handling
function setupFileUpload() {
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('pdf-upload');
    const uploadedFilesContainer = document.getElementById('uploaded-files');
    
    // Click to upload
    uploadZone.addEventListener('click', () => {
        fileInput.click();
    });
    
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        handleFiles(files);
    });
}

function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    for (let file of files) {
        if (file.type === 'application/pdf') {
            uploadedFiles.push(file);
            addFileToDisplay(file);
        } else {
            showNotification('Only PDF files are allowed', 'error');
        }
    }
    updateStartButton();
}

function addFileToDisplay(file) {
    const uploadedFilesContainer = document.getElementById('uploaded-files');
    const fileElement = document.createElement('div');
    fileElement.className = 'uploaded-file';
    fileElement.innerHTML = `
        <i class="fas fa-file-pdf"></i>
        <span>${file.name}</span>
        <button class="remove-file" onclick="removeFile('${file.name}')">
            <i class="fas fa-times"></i>
        </button>
    `;
    uploadedFilesContainer.appendChild(fileElement);
}

function removeFile(fileName) {
    uploadedFiles = uploadedFiles.filter(file => file.name !== fileName);
    
    // Remove from display
    const fileElements = document.querySelectorAll('.uploaded-file');
    fileElements.forEach(element => {
        if (element.textContent.includes(fileName)) {
            element.remove();
        }
    });
    
    updateStartButton();
}

function updateStartButton() {
    const websiteUrl = document.getElementById('website-url').value.trim();
    const hasFiles = uploadedFiles.length > 0;
    const startBtn = document.getElementById('start-processing-btn');
    
    startBtn.disabled = !websiteUrl && !hasFiles;
}

// Website URL validation
function setupWebsiteValidation() {
    const websiteInput = document.getElementById('website-url');
    websiteInput.addEventListener('input', updateStartButton);
}

// Data Processing Functions
async function startDataProcessing() {
    const websiteUrl = document.getElementById('website-url').value.trim();
    
    if (!websiteUrl && uploadedFiles.length === 0) {
        showNotification('Please provide a website URL or upload PDF files', 'error');
        return;
    }
    
    try {
        // Step 1: Create onboarding session
        console.log('Creating onboarding session...');
        const sessionResponse = await ApiClient.post('/onboarding/start', {
            initial_context: `Website: ${websiteUrl || 'None'}, PDFs: ${uploadedFiles.length} files`
        });
        
        currentSession = {
            sessionId: sessionResponse.session_id,
            agentId: sessionResponse.agent_id,
            firstQuestion: sessionResponse.first_question
        };
        
        console.log('Session created:', currentSession);
        
        // Start async data processing in background (no UI feedback needed)
        processDataInBackground(websiteUrl);
        
        // Move to agent identity step (step 2)
        currentStep = 2;
        updateProgress();
        showCurrentStep();
        
    } catch (error) {
        console.error('Error starting data processing:', error);
        showNotification('Failed to start processing. Please try again.', 'error');
    }
}

// New step navigation function
function nextStep() {
    if (validateCurrentStep()) {
        currentStep++;
        updateProgress();
        showCurrentStep();
        
        // Load data for specific steps
        if (currentStep === 3) {
            loadVoiceOptions();
        } else if (currentStep === 4) {
            loadToolOptions();
        } else if (currentStep === 5) {
            startInterview();
        }
    }
}

function validateCurrentStep() {
    switch(currentStep) {
        case 2: // Identity step
            const agentName = document.getElementById('agent-name').value.trim();
            const agentRole = document.getElementById('agent-role').value.trim();
            if (!agentName || !agentRole) {
                showNotification('Please fill in agent name and role', 'error');
                return false;
            }
            return true;
        case 3: // Voice step
            if (!selectedVoice) {
                showNotification('Please select a voice', 'error');
                return false;
            }
            return true;
        case 4: // Tools step
            if (selectedTools.length === 0) {
                showNotification('Please select at least one tool', 'error');
                return false;
            }
            return true;
        default:
            return true;
    }
}

// Load voice options
async function loadVoiceOptions() {
    try {
        const response = await ApiClient.get('/onboarding/voice-options');
        availableVoices = response.voices;
        renderVoiceOptions();
    } catch (error) {
        console.error('Error loading voice options:', error);
        showNotification('Failed to load voice options', 'error');
    }
}

function renderVoiceOptions() {
    const voiceGrid = document.getElementById('voice-grid');
    voiceGrid.innerHTML = availableVoices.map(voice => `
        <div class="voice-option ${voice.id === selectedVoice ? 'selected' : ''}" onclick="selectVoice('${voice.id}')">
            <div class="voice-info">
                <h4>${voice.name}</h4>
                <p>${voice.description}</p>
            </div>
            <button class="btn btn-ghost btn-small" onclick="event.stopPropagation(); playVoicePreview('${voice.id}')">
                <i class="fas fa-play"></i>
                Preview
            </button>
        </div>
    `).join('');
}

function selectVoice(voiceId) {
    selectedVoice = voiceId;
    document.querySelectorAll('.voice-option').forEach(option => {
        option.classList.remove('selected');
    });
    document.querySelector(`[onclick="selectVoice('${voiceId}')"]`).classList.add('selected');
}

function playVoicePreview(voiceId) {
    // For now, show notification - will implement with static audio files later
    showNotification(`Playing ${voiceId} voice preview...`, 'info');
}

// Load tool options
async function loadToolOptions() {
    try {
        const response = await ApiClient.get('/onboarding/tool-options');
        availableTools = response.tools;
        renderToolOptions();
    } catch (error) {
        console.error('Error loading tool options:', error);
        showNotification('Failed to load tool options', 'error');
    }
}

function renderToolOptions() {
    const toolsGrid = document.getElementById('tools-grid');
    toolsGrid.innerHTML = availableTools.map(tool => `
        <label class="tool-option ${tool.required ? 'required' : ''}">
            <input type="checkbox" name="tools" value="${tool.id}" 
                   ${tool.required ? 'checked disabled' : ''} 
                   onchange="toggleTool('${tool.id}')">
            <div class="tool-info">
                <h4>${tool.name} ${tool.required ? '<span class="required-badge">Required</span>' : ''}</h4>
                <p>${tool.description}</p>
                <span class="tool-category">${tool.category}</span>
            </div>
        </label>
    `).join('');
    
    // Initialize with required tools
    selectedTools = availableTools.filter(tool => tool.required).map(tool => tool.id);
}

function toggleTool(toolId) {
    if (selectedTools.includes(toolId)) {
        selectedTools = selectedTools.filter(id => id !== toolId);
    } else {
        selectedTools.push(toolId);
    }
}

// Complete enhanced onboarding
async function completeEnhancedOnboarding() {
    if (!validateCurrentStep()) return;
    
    try {
        // Collect all configuration
        const identityConfig = {
            agent_name: document.getElementById('agent-name').value.trim(),
            agent_role: document.getElementById('agent-role').value.trim(),
            greeting_message: document.getElementById('greeting-message').value.trim() || null
        };
        
        const voiceConfig = {
            voice_id: selectedVoice,
            personality: document.getElementById('personality').value,
            tone: document.getElementById('tone').value,
            speaking_speed: document.getElementById('speaking-speed').value,
            response_style: document.getElementById('response-style').value
        };
        
        const escalationTriggers = Array.from(document.querySelectorAll('input[name="escalation"]:checked'))
            .map(cb => cb.value);
        
        const toolsConfig = {
            enabled_tools: selectedTools,
            escalation_triggers: escalationTriggers,
            special_instructions: document.getElementById('special-instructions').value.trim() || null
        };
        
        // Store configuration globally for later use
        window.currentConfig = {
            agent_name: identityConfig.agent_name,
            business_type: extractBusinessTypeFromQA() || 'General Business', // Extract from Q&A or use default
            agent_role: identityConfig.agent_role,
            voice_id: voiceConfig.voice_id,
            enabled_tools: toolsConfig.enabled_tools
        };
        
        const configRequest = {
            session_id: currentSession.sessionId,
            identity_config: identityConfig,
            voice_config: voiceConfig,
            tools_config: toolsConfig
        };
        
        // Move to interview step first
        currentStep = 5;
        updateProgress();
        showCurrentStep();
        
        // Start interview with stored configuration
        currentSession.finalConfig = configRequest;
        startInterview();
        
    } catch (error) {
        console.error('Error collecting configuration:', error);
        showNotification('Failed to save configuration. Please try again.', 'error');
    }
}

async function processDataInBackground(websiteUrl) {
    try {
        // Prepare form data
        const formData = new FormData();
        
        if (websiteUrl) {
            formData.append('website_url', websiteUrl);
        }
        
        if (uploadedFiles.length > 0) {
            // For now, just use the first PDF file
            formData.append('pdf_file', uploadedFiles[0]);
        }
        
        // Start data processing in background - FIRE AND FORGET (DON'T AWAIT)
        console.log('Starting background data processing...');
        ApiClient.postFormData(`/data/process-data/${currentSession.sessionId}`, formData)
            .then(response => {
                if (response.success) {
                    console.log('Background processing started successfully:', response);
                } else {
                    console.error('Background processing failed:', response.error);
                }
            })
            .catch(error => {
                console.error('Error in background processing:', error);
                // Don't show error to user since this is background process
            });
        
    } catch (error) {
        console.error('Error setting up background processing:', error);
    }
}

// Interview Functions
async function startInterview() {
    questionCount = 1;
    
    // Display first question
    displayQuestion(currentSession.firstQuestion, questionCount);
}

function displayQuestion(question, questionNumber) {
    document.getElementById('question-number').textContent = questionNumber;
    document.getElementById('question-text').textContent = question;
    document.getElementById('answer-input').value = '';
    document.getElementById('answer-input').focus();
}

async function submitAnswer() {
    const answer = document.getElementById('answer-input').value.trim();
    
    if (!answer) {
        showNotification('Please provide an answer before continuing', 'error');
        return;
    }

    // Show thinking animation
    showThinkingAnimation(true);
    
    try {
        const response = await ApiClient.post('/onboarding/answer', {
            session_id: currentSession.sessionId,
            question_number: questionCount,
            answer: answer
        });
        
        if (response.is_complete) {
            // Interview complete, move to completion
            await completeOnboarding();
        } else {
            // Show next question
            questionCount++;
            displayQuestion(response.next_question, questionCount);
        }
        
    } catch (error) {
        console.error('Error submitting answer:', error);
        showNotification('Failed to submit answer. Please try again.', 'error');
    } finally {
        // Hide thinking animation
        showThinkingAnimation(false);
    }
}

// Completion Functions
async function completeOnboarding() {
    try {
        // Get configuration data from global variables instead of DOM elements
        // These should be set during the configuration steps
        let agentName, businessType, agentRole;
        
        // Try to get from configuration stored in previous steps
        if (window.currentConfig) {
            agentName = window.currentConfig.agent_name;
            businessType = window.currentConfig.business_type;
            agentRole = window.currentConfig.agent_role;
        } else {
            // Fallback: try to get from form elements that might exist
            const agentNameEl = document.querySelector('input#agent-name');
            const businessTypeEl = document.querySelector('input#business-type, select#business-type');
            const agentRoleEl = document.querySelector('input#agent-role, select#agent-role');
            
            agentName = agentNameEl ? agentNameEl.value : 'AI Assistant';
            businessType = businessTypeEl ? businessTypeEl.value : 'Business';
            agentRole = agentRoleEl ? agentRoleEl.value : 'Customer Service';
        }
        
        const selectedVoiceData = availableVoices.find(v => v.id === selectedVoice);
        
        const finalConfig = {
            agent_name: agentName || 'AI Assistant',
            business_type: businessType || 'Business',
            agent_role: agentRole || 'Customer Service',
            voice_id: selectedVoice || 'alloy',
            voice_name: selectedVoiceData?.name || 'Default Voice',
            enabled_tools: selectedTools || [],
            session_id: currentSession.sessionId
        };

        console.log('Sending config:', finalConfig); // Debug log

        // Show initialization step first
        currentStep = 6;
        updateProgress();
        showCurrentStep();
        
        // Update step 6 content to show initializing
        const step6Element = document.getElementById('step-completion');
        let animateSteps = null; // Declare outside the if block
        
        if (!step6Element) {
            console.error('Step 6 element not found');
            // Continue with API call anyway
        } else {
            step6Element.innerHTML = `
                <div class="step-content">
                    <div class="text-center">
                        <div class="initialization-spinner">
                            <div class="spinner"></div>
                        </div>
                        <h2 style="color: #2c3e50; margin: 2rem 0 1rem 0;">🤖 Initializing Your Voice Agent</h2>
                        <p style="color: #666; font-size: 1.1rem; margin-bottom: 1.5rem;">Our meta agent is configuring your voice assistant with advanced AI capabilities...</p>
                    
                    <div class="initialization-steps">
                        <div class="init-step active">
                            <div class="init-step-icon">🧠</div>
                            <div class="init-step-text">Processing personality traits</div>
                        </div>
                        <div class="init-step">
                            <div class="init-step-icon">💬</div>
                            <div class="init-step-text">Generating conversation patterns</div>
                        </div>
                        <div class="init-step">
                            <div class="init-step-icon">🎯</div>
                            <div class="init-step-text">Configuring business context</div>
                        </div>
                        <div class="init-step">
                            <div class="init-step-icon">🛠️</div>
                            <div class="init-step-text">Setting up tools & capabilities</div>
                        </div>
                    </div>
                    
                    <div class="agent-preview">
                        <h3>Agent Preview</h3>
                        <div class="preview-card">
                            <div class="preview-name">${agentName}</div>
                            <div class="preview-role">${agentRole} for ${businessType}</div>
                            <div class="preview-voice">Voice: ${selectedVoiceData?.name || 'Default'}</div>
                            <div class="preview-tools">${selectedTools?.length || 0} tools enabled</div>
                        </div>
                    </div>
                </div>
            </div>
            `;
            
            // Add CSS for initialization animation
            const initStyles = document.createElement('style');
            initStyles.textContent = `
                .initialization-spinner {
                    margin: 2rem 0;
                }
                
                .spinner {
                    width: 60px;
                    height: 60px;
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #3498db;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .initialization-steps {
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
                    max-width: 400px;
                    margin: 2rem auto;
                }
                
                .init-step {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                    padding: 0.8rem;
                    border-radius: 8px;
                    background: #f8f9fa;
                    transition: all 0.3s ease;
                    opacity: 0.5;
                }
                
                .init-step.active {
                    background: #e3f2fd;
                    opacity: 1;
                    transform: scale(1.02);
                }
                
                .init-step-icon {
                    font-size: 1.5rem;
                    width: 40px;
                    text-align: center;
                }
                
                .init-step-text {
                    font-weight: 500;
                    color: #2c3e50;
                }
                
                .agent-preview {
                    margin-top: 2rem;
                }
                
                .preview-card {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    margin-top: 1rem;
                }
                
                .preview-name {
                    font-size: 1.4rem;
                    font-weight: bold;
                    margin-bottom: 0.5rem;
                }
                
                .preview-role, .preview-voice, .preview-tools {
                    margin: 0.3rem 0;
                    opacity: 0.9;
                }
            `;
            document.head.appendChild(initStyles);
            
            // Animate through initialization steps
            const initSteps = document.querySelectorAll('.init-step');
            let currentInitStep = 0;
            
            animateSteps = setInterval(() => {
                if (currentInitStep < initSteps.length) {
                    initSteps[currentInitStep].classList.add('active');
                    currentInitStep++;
                }
            }, 800);
        }
        
        // Call the backend
        const response = await ApiClient.post('/complete', finalConfig);
        
        // Clear animation interval if it exists
        if (typeof animateSteps !== 'undefined' && animateSteps) {
            clearInterval(animateSteps);
        }
        
        if (response.success) {
            // Show completion
            setTimeout(() => {
                if (step6Element) {
                    step6Element.innerHTML = `
                    <div class="step-content">
                        <div class="text-center">
                            <div class="success-animation">✅</div>
                            <h2 style="color: #27ae60; margin: 2rem 0 1rem 0;">🎉 Agent Successfully Created!</h2>
                            <p style="color: #666; font-size: 1.1rem; margin-bottom: 2rem;">Your intelligent voice agent is ready to assist your customers.</p>
                            
                            <div class="agent-summary">
                                <h3>${agentName}</h3>
                                <p>${agentRole} configured with ${selectedVoiceData?.name || 'voice'} and ${selectedTools.length} tools</p>
                                <p class="status">Status: ${response.status === 'initializing' ? 'Finalizing configuration...' : 'Ready to deploy'}</p>
                            </div>
                            
                            <div class="completion-actions">
                                <button onclick="window.location.href='dashboard.html'" class="btn btn-primary">
                                    🚀 Go to Dashboard
                                </button>
                                <button onclick="startNewAgent()" class="btn btn-secondary">
                                    ➕ Create Another Agent
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
                // Add success animation styles
                const successStyles = document.createElement('style');
                successStyles.textContent = `
                    .success-animation {
                        font-size: 4rem;
                        animation: bounce 1s ease-in-out;
                    }
                    
                    @keyframes bounce {
                        0%, 20%, 60%, 100% { transform: translateY(0); }
                        40% { transform: translateY(-20px); }
                        80% { transform: translateY(-10px); }
                    }
                    
                    .agent-summary {
                        background: #f8f9fa;
                        padding: 1.5rem;
                        border-radius: 12px;
                        margin: 2rem 0;
                        border-left: 4px solid #27ae60;
                    }
                    
                    .agent-summary h3 {
                        color: #2c3e50;
                        margin-bottom: 0.5rem;
                    }
                    
                    .status {
                        font-weight: 500;
                        color: #3498db;
                    }
                    
                    .completion-actions {
                        display: flex;
                        gap: 1rem;
                        justify-content: center;
                        margin-top: 2rem;
                    }
                    
                    .completion-actions button {
                        padding: 12px 24px;
                        border: none;
                        border-radius: 8px;
                        font-size: 1rem;
                        font-weight: 500;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    }
                    
                    .btn-primary {
                        background: linear-gradient(135deg, #3498db, #2980b9);
                        color: white;
                    }
                    
                    .btn-primary:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
                    }
                    
                    .btn-secondary {
                        background: #ecf0f1;
                        color: #2c3e50;
                    }
                    
                    .btn-secondary:hover {
                        background: #d5dbdb;
                    }
                `;
                document.head.appendChild(successStyles);
                
                }
            }, 2000); // Show completion after 2 seconds
            
            currentSession.agentId = response.agent_id;
            showNotification('🎉 Voice agent created successfully!', 'success');
        }
        
    } catch (error) {
        console.error('Error completing onboarding:', error);
        showNotification('Failed to complete onboarding. Please try again.', 'error');
    }
}

function extractBusinessTypeFromQA() {
    // Try to extract business type from Q&A history
    if (currentSession && currentSession.questionHistory) {
        for (let qa of currentSession.questionHistory) {
            if (qa.question && qa.question.toLowerCase().includes('business') || 
                qa.question.toLowerCase().includes('company') ||
                qa.question.toLowerCase().includes('industry')) {
                return qa.answer || 'General Business';
            }
        }
    }
    return null;
}

function startNewAgent() {
    // Reset all state
    currentStep = 1;
    currentSession = {
        sessionId: null,
        agentId: null,
        questionHistory: [],
        isComplete: false
    };
    selectedVoice = 'alloy';
    selectedTools = [];
    
    // Clear forms
    document.getElementById('agent-name').value = '';
    document.getElementById('business-type').value = '';
    document.getElementById('agent-role').value = '';
    
    // Reset progress and show first step
    updateProgress();
    showCurrentStep();
    
    showNotification('Ready to create a new agent!', 'info');
}

// Completion Actions

// Utility Functions
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Add styles if not already added
    if (!document.querySelector('#notification-styles')) {
        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.textContent = `
            .notification {
                position: fixed;
                top: 2rem;
                right: 2rem;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                z-index: 10000;
                animation: slideInNotification 0.3s ease-out;
                max-width: 400px;
            }
            .notification-error {
                background: #fee2e2;
                border: 1px solid #fecaca;
                color: #dc2626;
            }
            .notification-success {
                background: #d1fae5;
                border: 1px solid #a7f3d0;
                color: #065f46;
            }
            .notification-info {
                background: #dbeafe;
                border: 1px solid #93c5fd;
                color: #1d4ed8;
            }
            .notification-content {
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            @keyframes slideInNotification {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(styles);
    }
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideInNotification 0.3s ease-out reverse';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

// Setup textarea auto-resize
function setupTextareaResize() {
    const textarea = document.getElementById('answer-input');
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
        
        // Allow Enter to submit
        textarea.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && e.ctrlKey) {
                submitAnswer();
            }
        });
    }
}

// UI Helper Functions
function showThinkingAnimation(show) {
    const thinkingAnimation = document.getElementById('thinking-animation');
    const submitBtn = document.getElementById('submit-answer-btn');
    const answerInput = document.getElementById('answer-input');
    
    if (show) {
        thinkingAnimation.style.display = 'flex';
        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.6';
        answerInput.disabled = true;
    } else {
        thinkingAnimation.style.display = 'none';
        submitBtn.disabled = false;
        submitBtn.style.opacity = '1';
        answerInput.disabled = false;
    }
}

// Dashboard Functions
async function loadDashboard() {
    console.log('Loading dashboard...');
    try {
        const response = await ApiClient.get('/agents');
        console.log('Dashboard response:', response);
        
        // Update stats in the dashboard content div
        const dashboardContent = document.getElementById('dashboard-content');
        if (dashboardContent && response.agents) {
            dashboardContent.innerHTML = `
                <div style="margin-top: 30px; background: white; color: black; padding: 20px; border-radius: 8px;">
                    <h2>Dashboard Stats</h2>
                    <p><strong>Total Agents:</strong> ${response.total || 0}</p>
                    <p><strong>Configured Agents:</strong> ${response.configured_count || 0}</p>
                    <p><strong>Active Agents:</strong> ${response.agents.filter(a => a.status === 'active').length}</p>
                    
                    <h3>Agents List:</h3>
                    ${response.agents.map(agent => `
                        <div style="border: 1px solid #ccc; margin: 10px 0; padding: 15px; border-radius: 8px;">
                            <h4>${agent.name ? `${agent.name} (Agent ${agent.id})` : `Agent ${agent.id}`}</h4>
                            <p><strong>Company:</strong> ${agent.company_name || 'No company set'}</p>
                            <p><strong>Status:</strong> ${agent.status}</p>
                            <p><strong>Role:</strong> ${agent.agent_role || 'Not set'}</p>
                            <p><strong>Voice:</strong> ${agent.voice_id || 'Not set'}</p>
                            <p><strong>Tools:</strong> ${agent.enabled_tools || 'None'}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        } else if (dashboardContent) {
            dashboardContent.innerHTML = `
                <div style="margin-top: 30px; background: white; color: black; padding: 20px; border-radius: 8px;">
                    <h2>No Agents Found</h2>
                    <p>Create your first voice agent to get started!</p>
                    <button onclick="showCreateAgent()" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">
                        Create Agent
                    </button>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        const dashboardContent = document.getElementById('dashboard-content');
        if (dashboardContent) {
            dashboardContent.innerHTML = `
                <div style="margin-top: 30px; background: white; color: red; padding: 20px; border-radius: 8px;">
                    <h2>Error Loading Dashboard</h2>
                    <p>Failed to load dashboard data: ${error.message}</p>
                </div>
            `;
        }
    }
}

function updateDashboardStats(data) {
    console.log('Updating dashboard stats with data:', data);
    
    const totalElement = document.getElementById('total-agents');
    const configuredElement = document.getElementById('configured-agents');
    const activeElement = document.getElementById('active-agents');
    
    if (totalElement) {
        totalElement.textContent = data.total || 0;
        console.log('Set total agents to:', data.total || 0);
    }
    
    if (configuredElement) {
        configuredElement.textContent = data.configured_count || 0;
        console.log('Set configured agents to:', data.configured_count || 0);
    }
    
    // Count active agents
    const activeCount = data.agents ? data.agents.filter(a => a.status === 'active').length : 0;
    if (activeElement) {
        activeElement.textContent = activeCount;
        console.log('Set active agents to:', activeCount);
    }
}

function renderAgentsGrid(agents) {
    // Temporarily disabled - using inline dashboard instead  
    console.log('renderAgentsGrid called but disabled for debugging');
    return;
    
    const grid = document.getElementById('agents-grid');
    const emptyState = document.getElementById('empty-state');
    
    if (!agents || agents.length === 0) {
        grid.innerHTML = '';
        emptyState.classList.remove('hidden');
        return;
    }
    
    emptyState.classList.add('hidden');
    
    grid.innerHTML = agents.map(agent => `
        <div class="agent-card" onclick="showAgentDetails(${agent.id})">
            <div class="agent-card-header">
                <div class="agent-info">
                    <h4>${agent.name ? `${agent.name} (Agent ${agent.id})` : `Agent ${agent.id}`}</h4>
                    <p class="agent-company">${agent.company_name || 'No company set'}</p>
                </div>
                <span class="agent-status ${agent.status}">${agent.status}</span>
            </div>
            
            <div class="agent-actions" onclick="event.stopPropagation()">
                <button class="btn btn-ghost" onclick="showNotification('Voice testing will be available in Phase 5', 'info')" ${!agent.is_configured ? 'disabled' : ''}>
                    <i class="fas fa-play"></i>
                    Test
                </button>
                <button class="btn btn-ghost" onclick="toggleAgentStatus(${agent.id}, '${agent.status}')">
                    <i class="fas fa-power-off"></i>
                    ${agent.status === 'active' ? 'Deactivate' : 'Activate'}
                </button>
                <button class="btn btn-ghost btn-danger" onclick="deleteAgent(${agent.id})">
                    <i class="fas fa-trash"></i>
                    Delete
                </button>
            </div>
        </div>
    `).join('');
}

async function showAgentDetails(agentId) {
    try {
        const response = await ApiClient.get(`/agents/${agentId}`);
        
        const modal = document.getElementById('agent-detail-modal');
        const modalName = document.getElementById('modal-agent-name');
        const modalBody = document.getElementById('agent-detail-content');
        
        modalName.textContent = response.name || `Agent ${agentId}`;
        
        modalBody.innerHTML = `
            <div class="agent-detail-section">
                <h4>Basic Information</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Company:</label>
                        <span>${response.company_name || 'Not set'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Status:</label>
                        <span class="agent-status ${response.status}">${response.status}</span>
                    </div>
                    <div class="detail-item">
                        <label>Personality:</label>
                        <span>${response.personality || 'Not set'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Tone:</label>
                        <span>${response.tone || 'Not set'}</span>
                    </div>
                </div>
            </div>
            
            ${response.system_prompt ? `
                <div class="agent-detail-section">
                    <h4>System Prompt</h4>
                    <div class="system-prompt">
                        ${response.system_prompt}
                    </div>
                </div>
            ` : ''}
        `;
        
        modal.classList.remove('hidden');
        
    } catch (error) {
        console.error('Error loading agent details:', error);
        showNotification('Failed to load agent details', 'error');
    }
}

function closeAgentModal() {
    document.getElementById('agent-detail-modal').classList.add('hidden');
}

async function refreshDashboard() {
    await loadDashboard();
    showNotification('Dashboard refreshed', 'success');
}

async function toggleAgentStatus(agentId, currentStatus) {
    try {
        const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
        
        await ApiClient.put(`/agents/${agentId}/status`, {
            status: newStatus
        });
        
        showNotification(`Agent ${newStatus === 'active' ? 'activated' : 'deactivated'}`, 'success');
        await loadDashboard();
        
    } catch (error) {
        console.error('Error updating agent status:', error);
        showNotification('Failed to update agent status', 'error');
    }
}

async function deleteAgent(agentId) {
    if (!confirm('Are you sure you want to delete this agent? This action cannot be undone.')) {
        return;
    }
    
    try {
        await ApiClient.delete(`/agents/${agentId}`);
        showNotification('Agent deleted successfully', 'success');
        await loadDashboard();
        
    } catch (error) {
        console.error('Error deleting agent:', error);
        showNotification('Failed to delete agent', 'error');
    }
}

// Global Functions (for HTML onclick handlers)
window.showCreateAgent = showCreateAgent;
window.showDashboard = showDashboard;
window.showLanding = showLanding;
window.goBack = goBack;
window.startDataProcessing = startDataProcessing;
window.nextStep = nextStep;
window.selectVoice = selectVoice;
window.playVoicePreview = playVoicePreview;
window.toggleTool = toggleTool;
window.completeEnhancedOnboarding = completeEnhancedOnboarding;
window.submitAnswer = submitAnswer;
window.removeFile = removeFile;
window.refreshDashboard = refreshDashboard;
window.showAgentDetails = showAgentDetails;
window.closeAgentModal = closeAgentModal;
window.toggleAgentStatus = toggleAgentStatus;
window.deleteAgent = deleteAgent;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Voice Agent Platform Frontend Initialized');
    
    // Setup event listeners
    setupFileUpload();
    setupWebsiteValidation();
    setupTextareaResize();
    
    // Check for hash navigation
    if (window.location.hash === '#onboarding') {
        showCreateAgent();
        window.location.hash = ''; // Clear hash
    }
    
    // Show landing page by default
    showLanding();
});
