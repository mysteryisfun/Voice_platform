# Voice Agent Platform - Execution Plan

## Project Summary & Current Status (September 2025)

**Voice Agent Deployment Platform** is an AI-powered system that enables businesses to create intelligent conversational voice agents through a streamlined onboarding process with LiveKit cloud infrastructure.

### ✅ **COMPLETED PHASES (1-3 @ 95%)**
- **Foundation Setup**: Complete FastAPI backend + Vite frontend infrastructure ✅
- **Data Pipeline**: ChromaDB vector storage, OpenAI integration, async processing ✅  
- **LiveKit Voice System**: Real cloud deployment with OpenAI Realtime API integration ✅ (95%)

### 🎯 **CURRENT STATUS: Critical 401 Authentication Bug**
The platform has complete voice infrastructure deployed on LiveKit Cloud with functional voice agents and testing interface. All components working except final voice connection authentication.

### Core Flow (95% Working)
1. ✅ **Business Input**: Company provides website URL + documents
2. ✅ **AI Onboarding**: Dynamic interview generates contextual questions
3. ✅ **Data Processing**: Parallel web scraping (Tavily) + PDF parsing into ChromaDB
4. ✅ **Agent Creation**: Knowledge-based agent configuration with business-specific data
5. ✅ **Voice Deployment**: LiveKit cloud infrastructure with agent worker registration
6. � **Voice Connection**: 401 Unauthorized preventing voice conversations
7. ⏳ **Production Polish**: Final debugging and optimization

---

## CRITICAL ISSUE - IMMEDIATE ATTENTION REQUIRED

### 🚨 Voice Connection 401 Unauthorized Error

#### Problem Summary:
- **Frontend**: Successfully creates voice sessions and receives valid tokens
- **Backend**: Generates proper JWT tokens with correct LiveKit credentials  
- **Agent Worker**: Successfully registered on LiveKit Cloud (ID: AW_JfznrqHbi3em)
- **LiveKit Connection**: Fails with 401 Unauthorized across all regions

#### Error Pattern:
```
WebSocket connection to 'wss://demo-bbxmozir.livekit.cloud/rtc?access_token=...' failed
GET https://demo-bbxmozir.livekit.cloud/rtc/validate?access_token=... 401 (Unauthorized)
Initial connection failed... Retrying with another region
```

#### Verified Working Components:
✅ **Backend Session Creation**: `/api/voice/2/session` returns valid session data  
✅ **JWT Token Generation**: Tokens created with proper permissions and expiration  
✅ **Agent Worker Registration**: Worker registered and running on LiveKit Cloud  
✅ **Frontend Integration**: ES module loading and session management functional  
✅ **Room Creation**: Unique room names generated correctly (agent-2-a956a9b2)

#### Root Cause Analysis:
❌ **Agent Worker Not Receiving Room Events**: No logs showing room join attempts  
❌ **Token Validation Mismatch**: Possible API key/secret inconsistency  
❌ **Room Dispatch Issue**: Agent worker not responding to room creation
---

## IMMEDIATE DEBUGGING STRATEGY

### 🎯 **STEP 1: Agent Worker Room Reception Analysis** (HIGH PRIORITY)
**Objective**: Determine if agent worker is receiving room join events

**Debug Actions**:
1. **Add Extensive Logging** to `backend/voice_agents/agent.py`:
```python
async def entrypoint(ctx: agents.JobContext):
    logger.info(f"🔥 ENTRYPOINT CALLED - Room: {ctx.room.name}")
    logger.info(f"🔥 Room participants: {len(ctx.room.participants)}")
    logger.info(f"🔥 Agent initialization starting...")
```

2. **Monitor Agent Worker Terminal** during connection attempts
3. **Test Room Creation** and verify worker logs show activity

### 🎯 **STEP 2: Token Validation Testing** (HIGH PRIORITY)  
**Objective**: Verify JWT token generation matches LiveKit expectations

**Debug Actions**:
1. **Token Payload Inspection** in `backend/routes/voice_control.py`:
```python
def generate_access_token(room_name, participant_name):
    payload = {
        "iss": LIVEKIT_API_KEY,
        "sub": participant_name,
        "aud": "livekit",
        "exp": now + 3600,
        "nbf": now - 10,
        "room": room_name,
        "permissions": permissions
    }
    logger.info(f"🔑 Token payload: {payload}")
    token = jwt.encode(payload, LIVEKIT_API_SECRET, algorithm="HS256")
    logger.info(f"🔑 Generated token: {token[:50]}...")
    return token
```

2. **Environment Variable Audit**:
```bash
# Verify these match LiveKit Cloud setup exactly
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxx
LIVEKIT_URL=wss://demo-bbxmozir.livekit.cloud
```

### 🎯 **STEP 3: Manual Connection Testing** (MEDIUM PRIORITY)
**Objective**: Test LiveKit connection outside of our application

**Debug Actions**:
1. **LiveKit CLI Testing** (if available)
2. **Token Validation via LiveKit API** directly
3. **Manual WebSocket Connection** with generated tokens

---

## SYSTEM ARCHITECTURE STATUS

### ✅ **FULLY OPERATIONAL COMPONENTS**

#### Backend Infrastructure:
- **FastAPI Server**: Running on port 8000 with all endpoints functional
- **Database**: SQLite with Agent and VoiceSession models operational
- **API Endpoints**: Voice session creation and management working
- **Token Generation**: JWT tokens with proper LiveKit format

#### Frontend Infrastructure:
- **Vite Dev Server**: Running on port 8080 with hot reloading
- **Voice Test Interface**: ES module LiveKit loading via Skypack CDN
- **Session Management**: Frontend successfully creates and manages sessions
- **WebRTC Integration**: Microphone access and audio handling working

#### LiveKit Integration:
- **Cloud Connection**: Successfully connected to demo-bbxmozir.livekit.cloud
- **Agent Worker**: Registered with ID "AW_JfznrqHbi3em" and running
- **Tool System**: 11 function tools properly decorated and ready
- **OpenAI Integration**: Realtime API configured for voice processing

### ❌ **SINGLE CRITICAL FAILURE POINT**

**LiveKit Room Authentication**: 401 Unauthorized on voice connection
- All preparation steps working correctly
- Final WebSocket connection failing authentication
- Requires investigation of token validation or room dispatch

---

## POST-FIX COMPLETION ROADMAP

### **IMMEDIATE TASKS (After 401 Fix)**

#### Voice System Testing (1 hour)
1. **End-to-End Conversation Testing**
   - Complete voice conversation with agent
   - Test all 11 function tools in conversation context
   - Verify agent personality and knowledge integration
   - Validate session management and cleanup

2. **Production Readiness** 
   - Add connection status indicators
   - Implement error handling for voice failures
   - Add user feedback for connection states
   - Document voice testing procedures

#### System Integration Testing (30 minutes)
1. **Dashboard Integration**
   - Connect agent cards to voice testing interface
   - Verify agent selection and URL parameter passing
   - Test multi-agent voice session management

2. **Database Verification**
   - Confirm voice session logging
   - Verify agent configuration persistence
   - Test session cleanup and management

### **NEXT PHASE: PRODUCTION DEPLOYMENT**

#### Phase 4: Advanced Features (2-3 weeks)
1. **Voice Widget Development**
   - Embeddable JavaScript widget for client websites
   - Custom styling and branding options
   - Integration documentation and code examples

2. **Analytics & Monitoring**
   - Voice conversation analytics dashboard
   - Session success rates and duration tracking
   - Agent performance metrics and optimization

3. **Scalability & Security**
   - Production LiveKit infrastructure setup
   - Multi-agent worker deployment
   - Security auditing and compliance
        # Main conversation processing logic
        pass
```

**Integration Points:**
- Connect to existing ChromaDB collections for RAG
- Use current OpenAI service for response generation
- Leverage existing agent configurations from database

#### Day 5: API Endpoints
**New routes in `backend/routes/voice.py`:**
```python
@router.post("/voice/token/{agent_id}")
async def generate_voice_token(agent_id: int):
    # Generate LiveKit access token for specific agent
    pass

@router.post("/voice/deploy/{agent_id}")  
async def deploy_voice_agent(agent_id: int):
    # Deploy agent to LiveKit room
    pass

@router.get("/voice/status/{agent_id}")
async def get_voice_status(agent_id: int):
    # Check deployment and session status
    pass

@router.post("/voice/webhook")
async def handle_livekit_webhook(request: Request):
    # Process LiveKit events and callbacks
    pass
```

### Week 2: Frontend Voice Interface

#### Day 1-2: LiveKit Client Integration
**Install Frontend Dependencies:**
```bash
cd frontend
npm install @livekit/components-js @livekit/components-styles
```

**Tasks:**
1. **Voice Test Interface**
   - Replace current placeholder "Test" button with functional voice testing
   - Implement LiveKit client connection
   - Real-time conversation display with transcript

2. **UI Components:**
   ```
   frontend/src/components/
   ├── VoiceTestModal.js       # Voice testing interface
   ├── ConversationDisplay.js  # Real-time transcript
   ├── VoiceControls.js        # Start/stop, mute controls
   └── WidgetPreview.js        # Widget customization preview
   ```

#### Day 3-4: Widget Generation System
**Tasks:**
1. **Widget Generator**
   - Customization panel (colors, positioning, branding)
   - Real-time preview of widget appearance
   - Generate embeddable JavaScript code

2. **Dashboard Integration**
   - Update agent cards to show voice deployment status
   - Add voice-specific configuration options
   - Display active voice sessions

#### Day 5: Testing and Integration
**Tasks:**
1. **End-to-End Testing**
   - Create voice agent through existing onboarding
   - Deploy to LiveKit and test voice interaction
   - Verify RAG responses using agent's knowledge base
   - Test widget generation and embedding

2. **Dashboard Updates**
   - Voice deployment status indicators
   - Active session monitoring
   - Performance metrics display

### Week 3: Production Polish

#### Day 1-2: Agent Tools Implementation
**Core Voice Agent Capabilities:**
```python
# backend/services/voice_tools.py
class VoiceAgentTools:
    async def knowledge_retrieval(self, query: str, agent_id: int):
        # Use existing ChromaDB collection for RAG
        pass
    
    async def lead_capture(self, conversation_context: dict):
        # Collect visitor information during conversation
        pass
    
    async def provide_business_info(self, info_type: str):
        # Business hours, contact info from knowledge base
        pass
```

#### Day 3-4: Widget Deployment
**Embeddable Widget Implementation:**
1. **Widget JavaScript Library**
   ```javascript
   // Static widget code that clients can embed
   class VoiceAgentWidget {
       constructor(config) {
           this.agentId = config.agentId;
           this.theme = config.theme;
           this.position = config.position;
       }
       
       async initialize() {
           // Connect to LiveKit room for specific agent
           // Handle voice session management
       }
   }
   ```

2. **Cross-Domain Integration**
   - Safe iframe implementation
   - CORS configuration for widget domains
   - Mobile-responsive design

#### Day 5: Performance Optimization
**Optimization Targets:**
- Voice latency < 500ms for natural conversation
- Efficient ChromaDB queries for real-time RAG
- Optimal LiveKit connection management
- Memory usage optimization for concurrent sessions

---

## Technical Implementation Details

### Integration with Existing Systems

#### Leveraging Current Infrastructure
✅ **ChromaDB Collections**: Each agent has isolated knowledge base ready for RAG  
✅ **Agent Management**: Dashboard provides interface for voice deployment  
✅ **OpenAI Integration**: GPT-4o mini setup ready for voice response generation  
✅ **Async Processing**: Current patterns applicable to voice session management  

#### Voice Data Flow
```
Browser → LiveKit Client → LiveKit Room → Voice Agent →
ChromaDB RAG → OpenAI Response → TTS → Browser
```

### Development Environment Setup

#### Backend Requirements
```python
# Additional dependencies for voice functionality
livekit-agents==0.8.0      # Core voice agent framework
livekit-api==0.5.0         # Room management and tokens
```

#### Frontend Requirements
```javascript
// LiveKit client libraries
@livekit/components-js      // Voice session components
@livekit/components-styles  // UI styling for voice interface
```

#### Environment Variables
```bash
# Add to .env file
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_secret
LIVEKIT_WS_URL=wss://your-project.livekit.cloud
```

---

## Success Metrics

### Phase 5 Completion Criteria
- [ ] Voice agents can be deployed to LiveKit rooms
- [ ] Real-time voice conversations using agent knowledge bases
- [ ] Working widget generation with embeddable code
- [ ] Voice testing interface in dashboard
- [ ] End-to-end voice session from onboarding to deployment

### Performance Targets
- **Voice Latency**: < 500ms response time
- **Knowledge Accuracy**: RAG responses using agent-specific data
- **Session Stability**: Reliable voice connections
- **Widget Integration**: Cross-domain embedding functionality

---

## Risk Mitigation

### Technical Risks
1. **LiveKit Learning Curve**: Allocate time for SDK familiarization
2. **Voice Quality**: Test thoroughly with different audio conditions
3. **Latency Issues**: Optimize RAG queries and response generation
4. **Cross-Domain Security**: Ensure safe widget embedding

### Mitigation Strategies
- Start with simple voice echo test before full RAG integration
- Use existing agent knowledge bases to minimize data pipeline changes
- Implement comprehensive error handling for voice session failures
- Test widget embedding on multiple domains and devices

---

## Post-Phase 5 Roadmap

### Phase 6: Advanced Features (Week 4-5)
- Calendar integration for appointment booking
- Advanced analytics and conversation insights
- Enhanced agent tools and capabilities
- Multi-language support

### Phase 7: Production Deployment (Week 6)
- Performance optimization and scaling
- Security hardening and compliance
- Documentation and deployment guides
- User onboarding and support materials

**Current State**: Platform foundation complete, ready for voice integration development in next session.
   - Context building from previous answers
   ```

3. **Web Scraping Service**
   ```
   Tasks:
   - Tavily API integration for website crawling
   - Content extraction and cleaning utilities
   - Async processing for multiple URLs
   - Error handling for failed scrapes
   ```

4. **PDF Processing**
   ```
   Tasks:
   - PDF text extraction (PyPDF2 or similar)
   - Document structure analysis
   - Content chunking for vector storage
   - File upload handling
   ```

### Frontend Data Interface
1. **Onboarding Flow UI**
   ```
   Tasks:
   - Multi-step form component
   - Progress indicator
   - File upload interface for PDFs
   - Dynamic question rendering
   ```

2. **Status Monitoring**
   ```
   Tasks:
   - Processing status displays
   - Progress tracking for async operations
   - Real-time updates via polling
   - Error state handling
   ```

### Testing Phase 2
```
Tests:
- Backend: ChromaDB stores and retrieves vectors correctly
- Backend: OpenAI generates relevant follow-up questions
- Backend: Tavily successfully scrapes test websites
- Backend: PDF processing extracts text properly
- Frontend: Onboarding flow captures user inputs
- Frontend: File uploads work correctly
- Integration: End-to-end data flow from input to vector storage
```

---

## Phase 3: Onboarding System (Week 5-6)

### Backend Onboarding Logic
1. **Session Management**
   ```
   Tasks:
   - POST /onboarding/start - Create new session
   - POST /onboarding/answer - Process responses, generate next question
   - GET /onboarding/status/{session_id} - Track progress
   - Session state persistence in database
   ```

2. **AI Question Engine**
   ```
   Tasks:
   - Context-aware question generation
   - Question categorization (business, agent config, requirements)
   - Completion criteria logic (8-12 questions)
   - Response validation and clarification
   ```

3. **Data Processing Pipeline**
   ```
   Tasks:
   - POST /onboarding/upload-pdf - Handle document uploads
   - Async web scraping trigger on URL submission
   - Parallel processing coordinator
   - Progress tracking and status updates
   ```

4. **Agent Configuration**
   ```
   Tasks:
   - POST /onboarding/complete - Finalize agent creation
   - Agent prompt template generation
   - Business data consolidation
   - Agent metadata storage
   ```

### Frontend Onboarding Experience
1. **Dynamic Question Interface**
   ```
   Tasks:
   - Conversational UI for Q&A flow
   - Input validation and real-time feedback
   - Website URL input with validation
   - Document drag-and-drop interface
   ```

2. **Progress Management**
   ```
   Tasks:
   - Visual progress indicators
   - Processing status displays
   - Background task monitoring
   - Completion confirmation screen
   ```

### Testing Phase 3
```
Tests:
- Backend: Complete onboarding session from start to finish
- Backend: AI generates appropriate questions based on context
- Backend: Parallel processing handles web scraping + PDF upload
- Backend: Agent configuration generated correctly
- Frontend: Smooth onboarding user experience
- Frontend: Progress tracking works accurately
- Integration: Full onboarding creates usable agent configuration
```

---

## Phase 4: Agent Management (Week 7-8)

### Backend Agent Operations
1. **Agent CRUD Operations**
   ```
   Tasks:
   - GET /agents - List all created agents
   - GET /agents/{agent_id} - Get specific agent details
   - DELETE /agents/{agent_id} - Remove agent
   - Agent status management (created, deployed, active, inactive)
   ```

2. **Knowledge Base Management**
   ```
   Tasks:
   - Agent-specific vector store isolation
   - Knowledge base querying service
   - RAG implementation for context retrieval
   - Content update capabilities
   ```

3. **Agent Tools Implementation**
   ```
   Tasks:
   - Lead capture tool with database storage
   - Information retrieval tool using RAG
   - Basic appointment booking structure
   - Tool execution framework
   ```

### Frontend Agent Dashboard
1. **Agent Listing Interface**
   ```
   Tasks:
   - Grid/list view of all agents
   - Agent status indicators
   - Basic agent information display
   - Search and filter capabilities
   ```

2. **Agent Detail Views**
   ```
   Tasks:
   - Agent configuration overview
   - Knowledge base summary
   - Performance metrics placeholder
   - Edit/delete actions
   ```

### Testing Phase 4
```
Tests:
- Backend: All agent CRUD operations work correctly
- Backend: Knowledge base isolation between agents
- Backend: RAG retrieval returns relevant context
- Backend: Agent tools execute successfully
- Frontend: Agent dashboard displays correctly
- Frontend: Agent details accessible and accurate
- Integration: Agent management workflow complete
```

---

## Phase 5: LiveKit Voice Integration (Week 9-10)

### Backend LiveKit Setup
1. **LiveKit Integration**
   ```
   Tasks:
   - LiveKit Python SDK installation and setup
   - POST /livekit/token - Generate access tokens
   - Room management for voice sessions
   - Agent connection to LiveKit rooms
   ```

2. **Voice Agent Implementation**
   ```
   Tasks:
   - Real-time voice processing
   - Speech-to-text integration
   - Text-to-speech implementation
   - Agent response generation with RAG
   ```

3. **Tool Integration in Voice**
   ```
   Tasks:
   - Voice-activated lead capture
   - Spoken appointment booking
   - Knowledge retrieval through conversation
   - Session logging and analytics
   ```

4. **Widget Code Generation**
   ```
   Tasks:
   - GET /agents/{agent_id}/widget - Generate embeddable code
   - JavaScript widget template
   - LiveKit client integration
   - Customization options (styling, positioning)
   ```

### Frontend Voice Interface
1. **Voice Session Testing**
   ```
   Tasks:
   - Test interface for voice agents
   - Voice session controls (start/stop/mute)
   - Real-time conversation display
   - Session status monitoring
   ```

2. **Widget Preview**
   ```
   Tasks:
   - Widget code display and copy functionality
   - Live preview of embeddable widget
   - Customization controls
   - Integration instructions
   ```

### Testing Phase 5
```
Tests:
- Backend: LiveKit tokens generated correctly
- Backend: Voice agents connect to rooms successfully
- Backend: Speech processing works end-to-end
- Backend: Agent tools execute via voice commands
- Frontend: Voice interface functional
- Frontend: Widget code generates and works when embedded
- Integration: Complete voice conversation with RAG responses
```

---

## Phase 6: Calendar Integration & Advanced Tools (Week 11-12)

### Backend Advanced Features
1. **Calendar MCP Integration**
   ```
   Tasks:
   - Calendar MCP setup and configuration
   - Real-time availability checking
   - Appointment scheduling logic
   - Calendar event creation
   ```

2. **Enhanced Lead Management**
   ```
   Tasks:
   - Lead scoring and classification
   - Lead export functionality
   - Follow-up tracking
   - Integration with appointment data
   ```

3. **Analytics & Monitoring**
   ```
   Tasks:
   - Conversation analytics tracking
   - Agent performance metrics
   - Usage statistics collection
   - Basic reporting endpoints
   ```

### Frontend Advanced Dashboard
1. **Analytics Interface**
   ```
   Tasks:
   - Basic analytics dashboard
   - Lead management interface
   - Appointment scheduling overview
   - Performance metrics display
   ```

2. **Advanced Agent Configuration**
   ```
   Tasks:
   - Agent personality customization
   - Tool configuration interface
   - Advanced prompt editing
   - Deployment controls
   ```

### Testing Phase 6
```
Tests:
- Backend: Calendar integration books appointments successfully
- Backend: Lead capture stores complete information
- Backend: Analytics track conversations accurately
- Frontend: Analytics dashboard displays metrics
- Frontend: Advanced configuration options work
- Integration: Complete business workflow from onboarding to appointment booking
```

---

## Phase 7: Polish & Production Readiness (Week 13-14)

### Backend Optimization
1. **Performance & Reliability**
   ```
   Tasks:
   - Error handling and logging improvements
   - Rate limiting implementation
   - Database query optimization
   - Memory usage optimization for ChromaDB
   ```

2. **API Documentation**
   ```
   Tasks:
   - FastAPI automatic documentation
   - Endpoint testing and validation
   - Response format standardization
   - Error response consistency
   ```

### Frontend Polish
1. **UI/UX Improvements**
   ```
   Tasks:
   - Visual design polish and consistency
   - Loading states and animations
   - Error message improvements
   - Mobile responsiveness testing
   ```

2. **User Experience**
   ```
   Tasks:
   - Onboarding flow optimization
   - Help documentation and tooltips
   - Keyboard shortcuts and accessibility
   - Browser compatibility testing
   ```

### Testing Phase 7
```
Tests:
- Performance: Load testing with multiple concurrent users
- Reliability: Error handling under various failure conditions
- UI/UX: Complete user journey testing
- Compatibility: Cross-browser and device testing
- Documentation: API documentation accuracy and completeness
```

---

## Development Guidelines

### Daily Development Process
1. **Morning Setup**
   - Activate conda environment: `.venv/Scripts/activate`
   - Pull latest changes from repository
   - Review current phase tasks and priorities

2. **Development Cycle**
   - Implement backend functionality first
   - Test backend endpoints thoroughly
   - Implement corresponding frontend features
   - Test integration between frontend and backend
   - Commit working features incrementally

3. **Testing Strategy**
   - Unit tests for individual functions
   - Integration tests for API endpoints
   - End-to-end tests for complete workflows
   - Manual testing for UI/UX validation

### Quality Assurance
- **Code Standards**: 4 spaces for Python, 2 spaces for JavaScript
- **Documentation**: Docstrings for all functions, API endpoint documentation
- **Error Handling**: Comprehensive error catching and user-friendly messages
- **Version Control**: Meaningful commit messages, feature branches for major changes

### Risk Mitigation
- **External API Dependencies**: Implement fallback mechanisms and proper error handling
- **Data Processing**: Validate all inputs and handle edge cases
- **Performance**: Monitor memory usage and implement caching where appropriate
- **User Experience**: Test with various input types and edge cases

This execution plan provides a structured approach to building the Voice Agent Platform with clear testing milestones at each phase to ensure quality and functionality before proceeding to the next development stage.
