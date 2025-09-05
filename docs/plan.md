# Voice Agent Platform - Master Plan

## Project Overview

**Platform Name**: Voice Agent Deployment Platform  
**Purpose**: AI-powered platform that creates, configures, and deploys conversational voice agents for businesses  
**Architecture**: Python FastAPI backend + Simple npm frontend + LiveKit voice infrastructure  
**Current Status**: Phase 5 (Voice Integration) - 85% Complete - Final debugging phase

## Current Platform Status (December 2024)

### ✅ **COMPLETED FUNCTIONALITY**
- **Full Agent Creation Pipeline**: Onboarding with AI-driven questions, document processing, web scraping ✅
- **Knowledge Base System**: ChromaDB with agent-specific isolation, 175+ knowledge chunks across 6 agents ✅
- **Professional Dashboard**: Agent management interface with CRUD operations, status controls, detail modals ✅
- **Async Processing**: Fire-and-forget data processing with proper status tracking ✅
- **API Infrastructure**: Complete FastAPI backend with health monitoring, error handling, logging filters ✅
- **LiveKit Voice Infrastructure**: Real cloud deployment, JWT tokens, voice agents, test interface ✅ (85%)

### 🎯 **CURRENT PHASE: Final Voice Integration Debugging**
The voice infrastructure is complete with LiveKit cloud integration. Currently debugging completion flow and finalizing test button integration.

## LiveKit Voice Integration Status (Phase 5 - 85% Complete)

### ✅ **COMPLETED VOICE COMPONENTS**

#### 1. LiveKit Cloud Setup ✅ COMPLETE
- **Cloud Infrastructure**: Real deployment on wss://demo-bbxmozir.livekit.cloud
- **Authentication**: PyJWT token generation for secure room access
- **Room Management**: Automatic room creation per voice session
- **API Keys**: Production LiveKit credentials configured

#### 2. Voice Agent Architecture ✅ COMPLETE
```python
# Implemented: voice_agents/voice_agent.py
class WebsiteVoiceAgent:
    - LiveKit agent integration with real-time processing
    - OpenAI realtime model integration (gpt-4o-realtime-preview)
    - VoiceAgentManager for session coordination
    - Real entrypoint function for agent deployment
```

#### 3. Agent Tools Framework ✅ COMPLETE  
```python
# Implemented: backend/services/agent_tools.py
class VoiceAgentTools:
    - search_knowledge_base(): ChromaDB integration
    - capture_lead(): Database lead storage  
    - search_web(): Tavily API integration
    - transfer_to_human(): Escalation handling
    - book_appointment(): Appointment scheduling
    - get_service_info(): Business information lookup
```

#### 4. Voice Control API ✅ COMPLETE
```python
# Implemented: backend/routes/voice_control.py
- POST /api/voice/{agent_id}/session: Create voice sessions
- Token generation with LiveKit JWT
- Room management and cleanup
- VoiceSession database tracking
```

#### 5. Frontend Voice Interface ✅ COMPLETE
```html
<!-- Implemented: frontend/voice-test.html -->
- LiveKit Web SDK integration
- Real microphone access and audio processing
- Agent-specific room connection (?agentId=123)
- Audio visualization and session management
```

#### 6. Meta Agent Configuration ✅ COMPLETE
```python
# Implemented: voice_agents/agent_builder.py
- LangChain-based agent configuration generation
- AgentPromptComponents structured output
- Business data integration for personalized agents
- Nested response handling for proper validation
```

### 🔧 **REMAINING ISSUES (Final 15%)**

#### Issue 1: Backend Startup Error 🚨 CRITICAL
**Problem**: Server crashes on startup with exit code 1
**Location**: Backend main.py or service imports
**Impact**: Cannot test voice functionality
**Priority**: URGENT - blocking all testing

#### Issue 2: Test Button Integration 🔧 HIGH
**Problem**: Agent card test button shows placeholder message
**Current**: `onclick="showNotification('Voice testing will be available in Phase 5')"`
**Required**: `onclick="window.open('voice-test.html?agentId=${agent.id}', '_blank')"`
**Impact**: Cannot access voice testing from dashboard

#### Issue 3: Agent Configuration Status 🔧 MEDIUM
**Problem**: Agents not marked as `is_configured=true` after creation  
**Impact**: Test button disabled, completion flow unclear
**Priority**: Affects user experience but voice infrastructure works

### 🎯 **COMPLETION ROADMAP**

#### Immediate Fixes (Today - 2 hours)
1. **Fix Backend Startup** (30 mins)
   - Debug import errors or dependency issues
   - Verify all services start correctly
   - Test API endpoints respond

2. **Connect Test Button** (15 mins)  
   - Update agent card onclick handler
   - Test agent selection and voice interface launch
   - Verify URL parameter passing

3. **Verify End-to-End Flow** (1 hour)
   - Complete onboarding → agent creation flow
   - Test voice interface connection and audio
   - Validate voice agent tools integration
   - Confirm real conversation capability

4. **Production Polish** (15 mins)
   - Add error handling for edge cases
   - Implement basic session cleanup
   - Add user feedback for voice connection status

#### Phase 6 Planning (Next Week)
1. **Voice Widget Integration**
   - Embeddable JavaScript widget for websites
   - Custom styling and branding options
   - Multi-language support

2. **Advanced Voice Features**
   - Voice agent analytics and conversation history
   - Advanced personality customization
   - Multi-agent conversation handling

3. **Production Deployment**
   - Production LiveKit credentials  
   - Scalable infrastructure setup
   - Monitoring and logging enhancement

---
    - TTS output with natural voice synthesis
    - Conversation state management
    - Agent tool execution (lead capture, knowledge retrieval)
```

#### 3. New API Endpoints
```
POST /api/voice/token/{agent_id}
- Generate LiveKit access token for specific agent
- Include agent-specific room configuration
- Return token + room details for frontend

POST /api/voice/deploy/{agent_id}
- Deploy agent to LiveKit room
- Connect to agent's ChromaDB collection
- Start voice processing pipeline
- Return deployment status

GET /api/voice/status/{agent_id}
- Check if agent is deployed and active
- Return room status and connection info
- Monitor voice session health

POST /api/voice/webhook
- Handle LiveKit events (participant join/leave, errors)
- Update agent status and session tracking
- Log conversation events for analytics
```

### Frontend Implementation Strategy

#### 1. Voice Testing Interface
- Add "Test Voice" button to agent dashboard (replace current placeholder)
- Implement LiveKit client connection for browser-based voice sessions
- Real-time conversation display with transcript
- Voice session controls (start/stop, mute, volume)

#### 2. Widget Generation System
- Widget customization panel (appearance, positioning, branding)
- Generate embeddable JavaScript code
- Widget preview functionality
- Copy-to-clipboard with installation instructions

#### 3. Agent Dashboard Enhancements
- Voice deployment status indicators
- Live session monitoring (active conversations)
- Voice-specific configuration options
- Performance metrics (voice quality, response time)

### Integration with Existing Systems

#### Leveraging Current Infrastructure
- **ChromaDB Collections**: Use existing agent-specific knowledge bases for RAG
- **Agent Management**: Extend current dashboard with voice capabilities
- **OpenAI Integration**: Use existing GPT-4o mini setup for response generation
- **Async Processing**: Apply current patterns to voice session management

#### Data Flow Integration
```
Voice Input → LiveKit STT → RAG Query (ChromaDB) → 
OpenAI Response → LiveKit TTS → Voice Output
```

### Agent Tools Implementation

#### Core Voice Agent Capabilities
1. **Knowledge Retrieval**: Answer questions using agent's ChromaDB collection
2. **Lead Capture**: Collect visitor information during voice conversations
3. **Business Information**: Provide hours, contact info, services from knowledge base
4. **Conversation Handoff**: Escalate to human when needed

#### Tool Execution Flow
- Voice agent detects intent (knowledge query, lead capture, etc.)
- Execute appropriate tool with conversation context
- Return structured response through TTS
- Update relevant databases (leads, analytics)

### Technical Implementation Details

#### LiveKit Python SDK Integration
```python
# Agent deployment process
async def deploy_voice_agent(agent_id: int):
    1. Get agent configuration from database
    2. Connect to agent's ChromaDB collection
    3. Create LiveKit room with agent-specific settings
    4. Start voice processing pipeline
    5. Register agent tools and capabilities
    6. Update deployment status
```

#### Voice Session Management
```python
# Real-time voice processing
async def handle_voice_session(room, participant):
    1. STT: Convert speech to text
    2. Intent Recognition: Understand user request
    3. RAG Query: Search agent's knowledge base
    4. Response Generation: Create contextual answer
    5. TTS: Convert response to speech
    6. Tool Execution: Handle lead capture, appointments
```

### Widget Deployment Strategy

#### Embeddable Widget Components
- **JavaScript Library**: Self-contained widget with LiveKit client
- **Customization Options**: Colors, positioning, agent personality
- **Cross-Domain Support**: Safe iframe or SDK integration
- **Mobile Responsive**: Works on all device types

#### Generated Widget Code Example
```html
<script src="https://platform.example.com/widget.js"></script>
<div id="voice-agent-widget" 
     data-agent-id="6" 
     data-position="bottom-right"
     data-theme="professional">
</div>
```

### Performance and Scalability

#### Optimization Targets
- **Voice Latency**: < 500ms response time for natural conversation
- **Concurrent Sessions**: Support multiple simultaneous voice conversations
- **Resource Efficiency**: Optimal use of LiveKit and OpenAI API calls
- **Knowledge Retrieval**: Fast ChromaDB queries for real-time responses

#### Monitoring and Analytics
- Voice session quality metrics
- Conversation completion rates
- Agent performance tracking
- Lead conversion analytics

***

## Technical Architecture

### Backend Stack
- **Framework**: FastAPI (Python)
- **AI/ML**: LangChain + OpenAI GPT-4o mini
- **Voice**: LiveKit Realtime Agents
- **Vector DB**: ChromaDB (in-memory for POC)
- **Web Scraping**: Tavily API
- **Validation**: Pydantic models
- **Database**: SQLite (local file)
- **Calendar Integration**: Calendar MCP

### Frontend Stack
- **Framework**: Simple npm-based application
- **UI**: Minimal dashboard interface
- **Communication**: REST API calls + polling for status
- **Features**: Agent listing, onboarding flow, widget code display

### External Services
- **LiveKit Cloud**: Voice session management and WebRTC
- **OpenAI API**: Dynamic question generation and conversation processing
- **Tavily API**: Business website crawling and content extraction

***

## System Workflow

### 1. Onboarding Process
1. Client accesses onboarding interface
2. AI generates dynamic questions based on business context
3. Parallel async processes: web scraping (Tavily) + PDF parsing
4. Data ingestion into ChromaDB vector store
5. Agent configuration and prompt template population
6. LiveKit agent deployment preparation
7. Widget code generation

### 2. Agent Deployment
1. LiveKit session initialization with custom tools
2. RAG-powered responses using ChromaDB knowledge base
3. Real-time voice conversation handling
4. Tool execution (lead capture, appointment booking, information retrieval)

### 3. Client Integration
1. Widget code provided to client
2. Embeddable on any website
3. Direct connection to deployed LiveKit agent

***

## API Specification

### Core Endpoints

#### Onboarding Flow
- `POST /onboarding/start` - Initialize new onboarding session
- `POST /onboarding/answer` - Submit user response, get next AI question
- `POST /onboarding/upload-pdf` - Upload business documents
- `POST /onboarding/complete` - Finalize configuration and start agent creation
- `GET /onboarding/status/{session_id}` - Check processing progress

#### Agent Management
- `GET /agents` - List all created agents
- `GET /agents/{agent_id}` - Get specific agent details
- `POST /agents/{agent_id}/deploy` - Deploy agent to LiveKit
- `GET /agents/{agent_id}/widget` - Get embeddable widget code
- `DELETE /agents/{agent_id}` - Remove agent

#### LiveKit Integration
- `POST /livekit/token` - Generate LiveKit access tokens
- `POST /livekit/webhook` - Handle LiveKit events
- `GET /livekit/rooms` - List active voice sessions

### Response Formats
- Standard JSON responses with status codes
- Async operation status tracking with progress indicators
- Error handling with descriptive messages

***

## Voice Agent Capabilities

### Core Tools Available

#### 1. RAG Knowledge Retrieval
- **Purpose**: Answer questions using business-specific knowledge
- **Data Sources**: Website content + uploaded PDFs
- **Implementation**: ChromaDB similarity search + context injection

#### 2. Lead Capture
- **Purpose**: Collect potential customer information
- **Data Collected**: Name, email, phone, company, requirements
- **Storage**: SQLite database with timestamp and agent association

#### 3. Appointment Booking
- **Purpose**: Schedule meetings/consultations
- **Integration**: Calendar MCP for real-time availability
- **Features**: Time slot suggestions, calendar integration, confirmation emails

### Agent Personality Framework
- **Tone Configuration**: Professional, friendly, casual, technical
- **Response Style**: Concise vs detailed explanations
- **Language Support**: Primary language with fallback options
- **Brand Voice**: Customizable terminology and communication patterns

***

## Dynamic Onboarding System

### AI Question Categories

#### Business Fundamentals
- Company name and industry vertical
- Core products/services description
- Target audience and customer demographics
- Business size and operational scope

#### Agent Configuration
- Primary use case selection (support, sales, information, booking)
- Desired agent personality and tone
- Conversation style preferences
- Agent naming and branding

#### Functional Requirements
- Business hours and availability windows
- Preferred response detail level
- Language and communication preferences
- Specific business terminology

#### Content Boundaries
- Topics to emphasize or avoid
- Industry compliance considerations
- Brand voice guidelines
- Escalation scenarios definition

### Question Flow Logic
- **Adaptive Questioning**: GPT-4o mini generates follow-ups based on previous responses
- **Context Building**: Each answer informs subsequent question generation
- **Completion Criteria**: Sufficient information for agent configuration (8-12 questions typically)
- **Validation**: Real-time response validation and clarification requests

***

## Data Processing Pipeline

### Web Scraping (Tavily)
- **Trigger**: Website URL provided during onboarding
- **Process**: Comprehensive site crawling and content extraction
- **Content Types**: Text content, product descriptions, FAQs, contact information
- **Storage**: Raw content chunking and vector embedding

### Document Processing
- **File Types**: PDF documents uploaded by clients
- **Extraction**: Text parsing and content structure analysis
- **Integration**: Combined with web content for comprehensive knowledge base
- **Indexing**: Vector embeddings for semantic search

### Vector Database Population
- **Technology**: ChromaDB in-memory storage
- **Embedding Model**: Compatible with LangChain integration
- **Retrieval**: Similarity search for relevant context injection
- **Updates**: Dynamic addition of new content sources

***

## Frontend Dashboard

### Core Features

#### Agent Management Interface
- **Agent Listing**: Grid view with agent names, status, and creation dates
- **Agent Details**: Configuration overview and performance metrics
- **Widget Access**: Copy-paste embeddable code generation
- **Status Monitoring**: Real-time deployment and availability status

#### Onboarding Interface
- **Progressive Form**: Step-by-step question flow
- **File Upload**: Drag-drop PDF document handling
- **Progress Tracking**: Visual indicators for processing stages
- **Preview Mode**: Agent configuration summary before deployment

#### Dashboard Analytics
- **Usage Metrics**: Basic conversation volume and duration
- **Agent Performance**: Response accuracy and user satisfaction
- **Lead Tracking**: Captured leads and appointment bookings

### User Experience Design
- **Minimal UI**: Clean, functional interface without complexity
- **Responsive**: Mobile-friendly design for accessibility
- **Real-time Updates**: Status polling and progress indicators
- **Error Handling**: Clear feedback for any processing issues

***

## Database Structure

### Core Data Entities
- **Agents**: Agent configuration, prompts, and deployment status
- **Onboarding Sessions**: Question-answer history and processing state
- **Vector Store**: Business knowledge base and content embeddings
- **Leads**: Captured customer information and interaction history
- **Appointments**: Scheduled meetings and calendar integration data

### Storage Strategy
- **SQLite**: Primary structured data storage
- **ChromaDB**: Vector embeddings and semantic search
- **File System**: PDF documents and temporary processing files
- **Memory**: Session management and real-time state

***

## Deployment Architecture

### POC Environment
- **Local Development**: Single machine deployment
- **Database**: SQLite file-based storage
- **Vector Store**: In-memory ChromaDB instance
- **External APIs**: LiveKit Cloud + OpenAI + Tavily

### Widget Deployment
- **Code Generation**: JavaScript snippet with LiveKit integration
- **Client Integration**: Embeddable on any website
- **Session Management**: Direct connection to deployed agents
- **Customization**: Styling and positioning options

***

## Security & Compliance

### POC Security Measures
- **No Authentication**: Simplified access for proof of concept
- **Data Isolation**: Agent-specific knowledge bases
- **API Rate Limiting**: Basic protection against abuse
- **Input Validation**: Pydantic model validation

### Future Considerations
- User authentication and authorization
- Data encryption and secure storage
- GDPR compliance and data retention policies
- API security and access control

***

## Performance Considerations

### Scalability Design
- **Async Processing**: Background tasks for data processing
- **Caching Strategy**: Frequent query result caching
- **Resource Management**: Efficient vector store operations
- **Connection Pooling**: Optimized database and API connections

### Monitoring Requirements
- **API Performance**: Response time and error rate tracking
- **Voice Session Quality**: LiveKit connection metrics
- **Resource Usage**: Memory and storage consumption
- **User Experience**: Onboarding completion rates and satisfaction

***

## Development Roadmap

### Phase 1: Core Infrastructure
- FastAPI backend setup with basic endpoints
- ChromaDB integration and vector operations
- OpenAI API integration for dynamic questioning
- Basic frontend dashboard structure

### Phase 2: Onboarding System
- AI-powered question generation flow
- Tavily web scraping integration
- PDF processing and content extraction
- Progress tracking and status management

### Phase 3: Voice Agent Deployment
- LiveKit integration and agent configuration
- Tool implementation (RAG, lead capture, appointments)
- Widget code generation and customization
- End-to-end testing and optimization

### Phase 4: Polish & Testing
- Frontend UI completion and styling
- Error handling and edge case management
- Performance optimization and monitoring
- Documentation and deployment preparation

This master plan provides comprehensive guidance for building the voice agent platform while maintaining focus on POC-level implementation with room for future scaling and enhancement.