# EXHAUSTIVE PROJECT ANALYSIS: Contact Center AI Agent System

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Complete Architecture](#2-complete-architecture)
3. [Complete File Structure](#3-complete-file-structure)
4. [Complete Technology Stack](#4-complete-technology-stack)
5. [Complete Database Schema](#5-complete-database-schema)
6. [Complete API Documentation](#6-complete-api-documentation)
7. [Predefined Reports](#7-predefined-reports)
8. [Agent System Details](#8-agent-system-details)
9. [Data Flow Diagrams](#9-data-flow-diagrams)
10. [Security Measures](#10-security-measures)
11. [Performance Optimizations](#11-performance-optimizations)
12. [Error Handling](#12-error-handling)
13. [Configuration Reference](#13-configuration-reference)
14. [Startup Sequence](#14-startup-sequence)
15. [Features Summary](#15-features-summary)

---

## 1. PROJECT OVERVIEW

### 1.1 Purpose
An **AI-powered contact center analytics platform** that enables:
- Natural language querying of call records and agent data
- Automatic Excel report generation
- Real-time streaming AI responses with visible thinking process
- Multi-database integration (MongoDB + MariaDB)

### 1.2 Product Name
**Azalio Deep Data Agent**

### 1.3 Core Value Proposition
- Eliminates need for SQL/NoSQL query knowledge
- Instant Excel report generation
- Real-time streaming responses
- Single interface for multiple databases

---

## 2. COMPLETE ARCHITECTURE

### 2.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js 16)                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐ │
│  │   Login Page   │  │   Chat Page    │  │  Components        │ │
│  │   /login       │  │   /chat        │  │  - MessageList     │ │
│  │                │  │                │  │  - ChatInput       │ │
│  │                │  │                │  │  - ThoughtProcess  │ │
│  │                │  │                │  │  - ChartRenderer   │ │
│  │                │  │                │  │  - Sidebar         │ │
│  └────────────────┘  └────────────────┘  └────────────────────┘ │
│                              │                                    │
│  ┌───────────────────────────┴───────────────────────────┐      │
│  │              STATE MANAGEMENT (Zustand)                │      │
│  │  ┌──────────────┐  ┌──────────────┐                   │      │
│  │  │  AuthStore   │  │  ChatStore   │                   │      │
│  │  │  - user      │  │  - messages  │                   │      │
│  │  │  - tokens    │  │  - wsId      │                   │      │
│  │  │  - login()   │  │  - streaming │                   │      │
│  │  │  - logout()  │  │  - connect() │                   │      │
│  │  └──────────────┘  └──────────────┘                   │      │
│  └───────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────┘
                              │
                    HTTP/REST │ WebSocket
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      BACKEND (Flask + Python)                     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                      ROUTES LAYER                            ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  ││
│  │  │  auth.py     │  │  chat.py     │  │  websocket.py    │  ││
│  │  │  /login      │  │  /download   │  │  /ws/chat        │  ││
│  │  │  /logout     │  │  /export     │  │  - streaming     │  ││
│  │  │  /session    │  │  /clear      │  │  - event loop    │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    AGENTS LAYER (LangGraph)                  ││
│  │                                                              ││
│  │  ┌────────────────────────────────────────────────────────┐ ││
│  │  │              SUPERVISOR AGENT (Orchestrator)           │ ││
│  │  │  - Routes queries to appropriate agent                 │ ││
│  │  │  - Passes through responses unchanged                  │ ││
│  │  │  - Handles greetings/small talk directly               │ ││
│  │  │  - Returns JSON: {summary, report_path, chart_data}    │ ││
│  │  └────────────────────────────┬───────────────────────────┘ ││
│  │                               │                              ││
│  │      ┌────────────────────────┼────────────────────────┐    ││
│  │      ▼                        ▼                        ▼    ││
│  │  ┌─────────────────┐  ┌─────────────────┐                   ││
│  │  │ DATA EXTRACTION │  │ VISUALISATION   │                   ││
│  │  │     AGENT       │  │     AGENT       │                   ││
│  │  │                 │  │                 │                   ││
│  │  │ - MongoDB MCP   │  │ - Chart.js JSON │                   ││
│  │  │ - MariaDB MCP   │  │ - bar/pie/line  │                   ││
│  │  │ - Excel export  │  │ - doughnut/etc  │                   ││
│  │  │ - Predefined    │  │                 │                   ││
│  │  │   queries       │  │                 │                   ││
│  │  └─────────────────┘  └─────────────────┘                   ││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                      TOOLS LAYER                             ││
│  │  ┌──────────────────┐  ┌──────────────────┐                 ││
│  │  │ mongodb_query_   │  │ mariadb_query_   │                 ││
│  │  │    tool.py       │  │    tool.py       │                 ││
│  │  │ - generate_      │  │ - generate_      │                 ││
│  │  │   reports()      │  │   mariadb_       │                 ││
│  │  │                  │  │   reports()      │                 ││
│  │  └──────────────────┘  └──────────────────┘                 ││
│  │  ┌──────────────────────────────────────────────────────┐   ││
│  │  │                excel_converter.py                     │   ││
│  │  │ - convert_ejson_to_excel()                            │   ││
│  │  │ - Handles nested docs, dates, large datasets          │   ││
│  │  └──────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   MongoDB MCP    │ │   MariaDB MCP    │ │  Session Files   │
│   Server (:4000) │ │   Server (:9001) │ │  (agent_files/)  │
│                  │ │                  │ │                  │
│ - Streamable HTTP│ │ - Streamable HTTP│ │ - sessions/      │
│ - READ-ONLY mode │ │ - READ-ONLY mode │ │   {ws_id}/       │
│                  │ │                  │ │     outputs/     │
└────────┬─────────┘ └────────┬─────────┘ └──────────────────┘
         │                    │
         ▼                    ▼
┌──────────────────┐ ┌──────────────────┐
│     MongoDB      │ │     MariaDB      │
│   (ccs_dev DB)   │ │   (ccs_dev DB)   │
│                  │ │                  │
│ Collections:     │ │ Tables:          │
│ - calling_cdr    │ │ - agent_details  │
│ - address_book   │ │ - agent_calling_ │
│ - customer_cdr   │ │   details        │
│ - campaign_      │ │ - smeReport      │
│   mapping        │ │ - whatsAppReport │
│ - customer_      │ │ - users          │
│   followup       │ │ - log_history    │
│ - agent_report_  │ │                  │
│   details        │ │                  │
└──────────────────┘ └──────────────────┘
```

---

## 3. COMPLETE FILE STRUCTURE

```
Contact_Center_Project/
│
├── app.py                              # Flask application entry point (line: 1-127)
│   ├── Creates Flask app with CORS
│   ├── Registers blueprints (auth, chat, websocket)
│   ├── Initializes MCP tools at startup
│   └── Runs server on port 8000
│
├── requirements.txt                    # Python dependencies (17 packages)
│
├── .env                                # Environment variables (gitignored)
├── .env.example                        # Environment template
│
├── README.md                           # Documentation (508 lines)
│
├── agents/
│   ├── __init__.py                     # Package exports
│   │
│   ├── supervisor_agent.py             # Supervisor Agent (line: 1-193)
│   │   ├── create_supervisor_agent(ws_id, session_folder, mcp_tools)
│   │   ├── Uses LangGraph for orchestration
│   │   ├── Routes to data_extraction_agent or visualisation_agent
│   │   ├── Uses MemorySaver for conversation persistence
│   │   └── Streams events via callback handler
│   │
│   ├── data_extraction_agent.py        # Data Extraction Agent (line: 1-148)
│   │   ├── create_data_extraction_agent(ws_id, session_folder, mcp_tools)
│   │   ├── Has access to MCP tools + custom report tools
│   │   ├── generate_reports (MongoDB)
│   │   ├── generate_mariadb_reports (MariaDB)
│   │   └── Returns JSON with summary + report_path
│   │
│   ├── visualisation_agent.py          # Visualization Agent (line: 1-76)
│   │   ├── create_visualisation_agent()
│   │   ├── Creates Chart.js configurations
│   │   └── Returns JSON with chart_data
│   │
│   └── mongo_mcp_client.py             # MCP Client Initialization (line: 1-85)
│       ├── load_mcp_tools() - loads tools once at startup
│       ├── Reads config/mcp.json
│       └── Uses langchain_mcp_adapters
│
├── routes/
│   ├── __init__.py                     # Package exports
│   │
│   ├── auth.py                         # Authentication routes (line: 1-85)
│   │   ├── POST /api/auth/login
│   │   │   └── Returns {token, username, status}
│   │   ├── POST /api/auth/logout
│   │   │   └── Invalidates session
│   │   └── POST /api/auth/session
│   │       └── Validates active session
│   │
│   ├── chat.py                         # Chat & Download routes (line: 1-156)
│   │   ├── POST /api/chat
│   │   │   └── Non-streaming chat (fallback)
│   │   ├── POST /api/chat/clear
│   │   │   └── Clears conversation history
│   │   ├── POST /api/chat/export-excel
│   │   │   └── Exports data to Excel
│   │   └── GET /api/chat/download/<path>
│   │       └── Serves Excel files with path traversal protection
│   │
│   └── websocket.py                    # WebSocket Handler (line: 1-312)
│       ├── WebSocket /ws/chat
│       ├── Creates session-specific agents per connection
│       ├── Streams events: connection, message, tool_start, tool_end, final, complete
│       ├── Transforms [DOWNLOAD:path] to full session path
│       └── 10ms event loop for responsive streaming
│
├── tools/
│   ├── __init__.py                     # Package exports
│   │
│   ├── excel_converter.py              # Excel Conversion Tool (line: 1-217)
│   │   ├── create_excel_converter_tool(session_id, session_folder)
│   │   ├── Handles EJSON date formats ($date)
│   │   ├── Flattens nested documents
│   │   ├── Uses write_only mode for memory efficiency
│   │   └── Returns [DOWNLOAD:outputs/filename.xlsx]
│   │
│   ├── mongodb_query_tool.py           # MongoDB Report Tool (line: 1-283)
│   │   ├── create_mongodb_query_tool(session_id, session_folder)
│   │   ├── MongoDBReportGenerator class
│   │   ├── Loads queries from config/queries.json
│   │   ├── Supports 9 predefined report types
│   │   ├── Date placeholder replacement
│   │   └── Returns summary + report_path
│   │
│   └── mariadb_query_tool.py           # MariaDB Report Tool (line: 1-321)
│       ├── create_mariadb_query_tool(session_id, session_folder)
│       ├── MariaDBQueryExecutor class
│       ├── Loads queries from config/mariadb_queries.json
│       ├── Supports 4 predefined report types
│       └── Returns summary + report_path
│
├── prompts/
│   ├── supervisor_system.txt           # Supervisor Agent Prompt (210 lines)
│   │   ├── Routing rules for delegation
│   │   ├── JSON output format requirements
│   │   ├── Pass-through rules for data agent responses
│   │   └── Chart handling rules
│   │
│   ├── data_agent_system.txt           # Data Extraction Agent Prompt (233 lines)
│   │   ├── Database schema definitions
│   │   ├── Tool selection priority
│   │   ├── Date handling with EJSON format
│   │   ├── Report generation rules
│   │   └── Connection error handling
│   │
│   └── visualisation_prompt.txt        # Visualization Agent Prompt (178 lines)
│       ├── Chart.js configuration format
│       ├── Chart type selection guidelines
│       ├── Color palette guidelines
│       └── Multiple charts support
│
├── config/
│   ├── mcp.json                        # MCP Server Configuration
│   │   ├── mongodb: http://127.0.0.1:4000/mcp
│   │   └── mariadb: http://127.0.0.1:9001/mcp
│   │
│   ├── queries.json                    # MongoDB Predefined Queries (1043 lines)
│   │   ├── calling_cdr_incoming (incoming calls with lookups)
│   │   ├── calling_cdr_outgoing (outgoing calls)
│   │   ├── manual_outbound_calls (call_mode=3)
│   │   ├── failed_calls (notpatched status)
│   │   ├── abandoned_calls
│   │   ├── auto_call_distribution (dialers)
│   │   ├── transfer_conference_calls
│   │   ├── callback_followup
│   │   └── list_wise_dialing_status
│   │
│   └── mariadb_queries.json            # MariaDB Predefined Queries (41 lines)
│       ├── agent_activity
│       ├── agent_status_report
│       ├── sms_report
│       └── whatsapp_report
│
├── utils/
│   ├── prompt_loader.py                # Prompt File Loader (4 lines)
│   │   └── load_prompt(path) -> str
│   │
│   └── websocket_manager.py            # WebSocket Connection Manager (97 lines)
│       ├── WebSocketManager class
│       ├── register(), connect(), disconnect()
│       ├── Message queuing for disconnected sessions
│       └── Automatic flush on reconnect
│
├── agent_files/                        # Generated Files Directory
│   └── sessions/
│       └── {ws_id}/                    # Session-specific folders
│           └── outputs/
│               └── *.xlsx              # Generated Excel reports
│
└── frontend/                           # Next.js Frontend Application
    │
    ├── package.json                    # Node.js dependencies
    │   ├── next: 16.0.5
    │   ├── react: 19.2.0
    │   ├── chart.js: ^4.5.1
    │   ├── zustand: ^5.0.8
    │   ├── react-markdown: ^10.1.0
    │   └── remark-gfm: ^4.0.1
    │
    ├── next.config.ts                  # Next.js configuration
    ├── tailwind.config.ts              # TailwindCSS 4 configuration
    ├── tsconfig.json                   # TypeScript configuration
    │
    ├── public/
    │   └── azalio_logo.png             # Application logo
    │
    └── src/
        │
        ├── app/
        │   ├── layout.tsx              # Root layout with Geist fonts
        │   ├── globals.css             # Global TailwindCSS styles
        │   ├── page.tsx                # Home redirect (auth check)
        │   │
        │   ├── login/
        │   │   └── page.tsx            # Login page (161 lines)
        │   │       ├── Email/password form
        │   │       ├── Remember me option
        │   │       └── Auto-redirect on auth
        │   │
        │   └── chat/
        │       └── page.tsx            # Main chat page (172 lines)
        │           ├── WebSocket connection management
        │           ├── Message handling
        │           ├── Conversation management
        │           └── Reconnection logic
        │
        ├── components/
        │   └── chat/
        │       ├── index.ts            # Component exports
        │       │
        │       ├── ChatInput.tsx       # Message input (186 lines)
        │       │   ├── Textarea with Enter submit
        │       │   └── Attachment button (UI only)
        │       │
        │       ├── MessageList.tsx     # Message display (408 lines)
        │       │   ├── WelcomeScreen with suggested prompts
        │       │   ├── MessageBubble component
        │       │   ├── LoadingIndicator with rotating messages
        │       │   ├── Smart scroll behavior
        │       │   └── Version navigation for retries
        │       │
        │       ├── MarkdownRenderer.tsx # Markdown rendering (136 lines)
        │       │   ├── ReactMarkdown with remark-gfm
        │       │   ├── Custom table styling
        │       │   └── ExportExcelButton integration
        │       │
        │       ├── ChartRenderer.tsx   # Chart.js rendering (201 lines)
        │       │   ├── Collapsible chart display
        │       │   ├── Download as PNG feature
        │       │   └── Responsive chart sizing
        │       │
        │       ├── ThoughtProcess.tsx  # AI thinking display (214 lines)
        │       │   ├── Collapsible thought process
        │       │   ├── Agent name badges
        │       │   ├── Function call display
        │       │   └── Live loading indicator
        │       │
        │       ├── ExportExcelButton.tsx # Download button (98 lines)
        │       │   ├── Downloads from /api/chat/download
        │       │   └── Error handling
        │       │
        │       ├── ResponseActions.tsx # Action buttons (257 lines)
        │       │   ├── Copy to clipboard
        │       │   ├── Thumbs up/down feedback
        │       │   ├── Retry button
        │       │   └── Version navigation
        │       │
        │       ├── ChatHeader.tsx      # Header bar (54 lines)
        │       │
        │       └── Sidebar.tsx         # Navigation sidebar (349 lines)
        │           ├── Collapsible sidebar
        │           ├── Conversation list
        │           ├── Connection status indicator
        │           └── User menu with logout
        │
        └── lib/
            ├── store.ts                # Barrel export for stores
            │
            ├── types.ts                # TypeScript types (72 lines)
            │   ├── User, AuthTokens, LoginResponse
            │   ├── ThinkingStep, ResponseVersion
            │   ├── Message, Conversation
            │
            ├── auth-store.ts           # Authentication state (144 lines)
            │   ├── Zustand store with persist middleware
            │   ├── login(), logout(), clearError()
            │   └── Auto-connect WebSocket on login
            │
            ├── chat-store.ts           # Chat state (697 lines)
            │   ├── Connection state (isConnected, wsId)
            │   ├── Streaming state (streamingContent, thinkingSteps)
            │   ├── Conversations management
            │   ├── connect(), reconnect(), disconnect()
            │   ├── sendQuery(), retryQuery()
            │   ├── startFakeStreaming() - word-by-word display
            │   └── Version management for retries
            │
            ├── chat-store-helpers.ts   # Helper functions
            │   ├── createThinkingStep()
            │   ├── createResponseVersion()
            │   ├── createAssistantMessage()
            │   ├── createErrorMessage()
            │   └── handleWebSocketMessage()
            │
            ├── websocket-message-handler.ts # Barrel export
            │
            ├── ws-message-handler.ts   # WebSocket Message Handler (491 lines)
            │   ├── WebSocketMessageHandler class
            │   ├── parseMessage(), filterMessage()
            │   ├── Message type callbacks
            │   ├── Storage for all message types
            │   └── Static type guard methods
            │
            ├── ws-types.ts             # WebSocket enums and interfaces
            │   ├── WSMessageType enum
            │   ├── MessageRole enum
            │   └── Message data interfaces
            │
            ├── ws-responses.ts         # WebSocket response types
            │
            ├── ws-filtered-types.ts    # Filtered message types
            │
            └── chart-types.ts          # Chart.js type definitions
```

---

## 4. COMPLETE TECHNOLOGY STACK

### 4.1 Backend Technologies

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Runtime** | Python | 3.11+ | Core runtime |
| **Web Framework** | Flask | 3.0+ | HTTP/REST API |
| **WebSocket** | Flask-Sock | 0.7+ | Real-time communication |
| **CORS** | Flask-CORS | 4.0+ | Cross-origin requests |
| **AI Framework** | LangChain | 1.0+ | Agent framework |
| **Orchestration** | LangGraph | 0.4+ | Multi-agent coordination |
| **LLM** | OpenAI GPT-5-mini | - | Language model |
| **LLM Binding** | langchain-openai | 0.3+ | OpenAI integration |
| **Agent Tools** | deepagents | 0.1+ | FilesystemMiddleware |
| **MCP Protocol** | mcp | 1.2+ | Model Context Protocol |
| **MCP Adapters** | langchain-mcp-adapters | 0.0.1+ | MCP tool integration |
| **MongoDB** | pymongo | 4.6+ | MongoDB driver |
| **Async MongoDB** | motor | 3.3+ | Async MongoDB |
| **MariaDB** | pymysql | - | MariaDB driver |
| **Data Validation** | Pydantic | 2.5+ | Schema validation |
| **Data Processing** | Pandas | - | Data manipulation |
| **Excel Generation** | openpyxl | - | Excel file creation |
| **Observability** | Langfuse | 2.0+ | Tracing & debugging |
| **Environment** | python-dotenv | 1.0+ | Environment loading |

### 4.2 Frontend Technologies

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Framework** | Next.js | 16.0.5 | React framework |
| **UI Library** | React | 19.2.0 | Component library |
| **Language** | TypeScript | 5 | Type safety |
| **State Management** | Zustand | 5.0.8 | Store management |
| **Styling** | TailwindCSS | 4 | Utility-first CSS |
| **Charts** | Chart.js | 4.5.1 | Data visualization |
| **Markdown** | react-markdown | 10.1.0 | Markdown rendering |
| **GFM Support** | remark-gfm | 4.0.1 | GitHub Flavored Markdown |
| **Fonts** | Geist, Geist_Mono | - | Typography |

### 4.3 Infrastructure

| Component | Technology | Port | Purpose |
|-----------|------------|------|---------|
| **Frontend Server** | Next.js dev server | 3000 | Development server |
| **Backend Server** | Flask | 8000 | API & WebSocket |
| **MongoDB MCP** | Node.js (npx) | 4000 | MongoDB MCP protocol |
| **MariaDB MCP** | Node.js | 9001 | MariaDB MCP protocol |
| **Database** | MongoDB 7.0+ | 27017 | NoSQL database |
| **Database** | MariaDB | - | Relational database |

---

## 5. COMPLETE DATABASE SCHEMA

### 5.1 MongoDB Collections (ccs_dev)

#### 5.1.1 calling_cdr (Main Call Records)

```javascript
{
  _id: ObjectId,
  sme_id: Number,                    // SME identifier (e.g., 20002124)
  session_id: String,                // Unique session identifier

  // Call Direction & Status
  call_direction: "INCOMING" | "OUTGOING",
  final_status: "patched" | "notpatched" | "abandoned" | "na",
  call_mode: Number,                 // 3 = manual outbound

  // Timing
  start_date_time: ISODate,          // Call start time (UTC)
  duration: Number,                  // Call duration in seconds
  ivr_duration: Number,              // IVR time
  queue_wait_duration: Number,       // Queue wait time
  after_call_wrapup_time: Number,    // Wrapup time

  // Customer Info
  customer_number: String,           // Customer phone number
  customer_ringing_duration: Number,
  customer_hangup_cause: String,

  // Agent Info
  agent_name: String,
  agent_number: String,
  agent_ringing_duration: Number,
  agent_hangup_cause: String,

  // Campaign & Queue
  campaign_name: String,
  campaign_id: String,
  campaign_type: String,             // power_dialer, progressive_dialer, etc.
  queue_name: String,
  call_flow_name: String,
  longcode: String,                  // Virtual number

  // Call Features
  on_call_hold_time: Number,
  hold_time_detail: Object,
  mute_duration: Number,
  mute_time_detail: Object,
  transferStatus: String,            // "1" = transferred
  conferenceStatus: String,          // "1" = conference
  conferenceDuration: Number,

  // Recording & Disposition
  recording_path: String,
  disposition_form_name: String,
  disconnected_by: String,
  final_dtmf: String,
  remarks: String,

  // Dialer Fields
  file_id: String,
  file_name: String,
  retry_count: Number
}
```

#### 5.1.2 address_book (Customer Information)

```javascript
{
  _id: ObjectId,
  customer_number_primary: String,   // Primary phone (join key)
  customer_name: String,
  // Additional customer fields...
}
```

#### 5.1.3 agent_report_details (Agent Performance)

```javascript
{
  _id: ObjectId,
  session_id: String,                // Join key with calling_cdr
  // Agent performance metrics...
}
```

#### 5.1.4 customer_followup (Callbacks)

```javascript
{
  _id: ObjectId,
  sme_id: Number,
  session_id: String,
  reminder_date_time: ISODate,
  // Follow-up details...
}
```

#### 5.1.5 campaign_mapping

```javascript
{
  _id: ObjectId,
  campaign_id: String,
  // Campaign configuration...
}
```

#### 5.1.6 customer_cdr

```javascript
{
  _id: ObjectId,
  // Customer-specific CDR data...
}
```

### 5.2 MariaDB Tables (ccs_dev)

#### 5.2.1 agent_details

```sql
agent_id          INT PRIMARY KEY,
agent_name        VARCHAR,
agent_email       VARCHAR,
sme_id            INT,
in_time           DATETIME,
out_time          DATETIME,
break_status      VARCHAR,
call_status       VARCHAR,
current_call_mode VARCHAR,
agent_login_type  VARCHAR,          -- 'fixed_schedule' or 'self_sign_in'
reporting_to      INT               -- FK to another agent
```

#### 5.2.2 agent_calling_details

```sql
agent_id              INT,
insert_date           DATE,
wrap_up_time          INT,
dialer_on_off_duration INT,
office_hours          INT,
lunch_hours           INT,
total_number_of_breaks INT,
hold_time             INT,
mute_time             INT,
total_call_duration   INT
```

#### 5.2.3 agent_details_timing

```sql
agent_id   INT,
days_week  VARCHAR,                 -- 'MON', 'TUE', etc.
in_time    TIME,
out_time   TIME
```

#### 5.2.4 log_history

```sql
agent_id          INT,
sme_id            INT,
action            VARCHAR,          -- 'login' or 'logout'
insert_date_time  DATETIME,
message           VARCHAR           -- Logout reason
```

#### 5.2.5 smeReport (SMS Reports)

```sql
agentName      VARCHAR,
dateTime       DATETIME,
campaign_name  VARCHAR,
status         INT,                 -- HTTP status code
type           VARCHAR              -- SMS state
```

#### 5.2.6 whatsAppReport

```sql
agentName      VARCHAR,
dateTime       DATETIME,
campaign_name  VARCHAR,
status         INT,
type           VARCHAR              -- WhatsApp state
```

#### 5.2.7 users

```sql
username        VARCHAR,
logged_in_time  DATETIME,
logged_out_time DATETIME
```

---

## 6. COMPLETE API DOCUMENTATION

### 6.1 Authentication Endpoints

#### POST /api/auth/login

**Purpose:** Authenticate user and get session token

**Request:**
```json
{
  "username": "demo",
  "password": "demo123"
}
```

**Response (200):**
```json
{
  "token": "uuid-v4-token",
  "username": "demo",
  "status": "success"
}
```

**Response (401):**
```json
{
  "error": "Invalid credentials",
  "status": "error"
}
```

---

#### POST /api/auth/logout

**Purpose:** End user session

**Request:**
```json
{
  "token": "your-session-token"
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```

---

#### POST /api/auth/session

**Purpose:** Validate active session

**Request:**
```json
{
  "token": "your-session-token"
}
```

**Response (200):**
```json
{
  "username": "demo",
  "login_time": "2025-12-24T10:30:00Z"
}
```

---

### 6.2 WebSocket Endpoint

#### WebSocket /ws/chat

**Purpose:** Real-time chat with streaming responses

**Connection:** `ws://localhost:8000/ws/chat`

**Client → Server Message:**
```json
{
  "type": "query",
  "token": "your-session-token",
  "data": {
    "message": "Give me incoming call report for today"
  }
}
```

**Server → Client Events:**

| Event Type | Description | Data |
|------------|-------------|------|
| `connection` | Connection established | `{type, ws_id}` |
| `query_received` | Query acknowledged | `{type}` |
| `message` | AI thinking/reasoning | `{type, data: {role, content, agent_name}}` |
| `tool_start` | Tool execution started | `{type, data: {tool}}` |
| `tool_end` | Tool execution completed | `{type, data: {tool, output}}` |
| `final` | Final response | `{type, data: {role, content, agent_name}}` |
| `complete` | Response complete | `{type}` |
| `error` | Error occurred | `{type, data: {message, code}}` |
| `pong` | Heartbeat response | `{type}` |

**Final Response Content Structure:**
```json
{
  "summary": "Markdown text with preview table",
  "report_path": "sessions/ws_id/outputs/report.xlsx",
  "chart_data": {
    "type": "pie",
    "data": {},
    "options": {}
  }
}
```

---

### 6.3 Chat Endpoints

#### POST /api/chat

**Purpose:** Non-streaming chat (fallback)

**Request:**
```json
{
  "token": "your-session-token",
  "message": "How many calls today?"
}
```

**Response:**
```json
{
  "reply": "{\"summary\":\"...\",\"report_path\":null}",
  "status": "success"
}
```

---

#### POST /api/chat/clear

**Purpose:** Clear conversation history

**Request:**
```json
{
  "token": "your-session-token"
}
```

---

#### POST /api/chat/export-excel

**Purpose:** Export arbitrary data to Excel

**Request:**
```json
{
  "token": "your-session-token",
  "data": [],
  "filename": "custom_report"
}
```

---

#### GET /api/chat/download/{path}

**Purpose:** Download generated Excel files

**Example:**
```
GET /api/chat/download/sessions/ws_abc123/outputs/incoming_calls_report.xlsx
```

**Security:**
- Path traversal protection
- Only serves from `agent_files/` directory

**Response:**
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename=report.xlsx`

---

## 7. PREDEFINED REPORTS

### 7.1 MongoDB Reports (config/queries.json)

| Report Name | Collection | Description |
|-------------|------------|-------------|
| `calling_cdr_incoming` | calling_cdr | Incoming calls with customer & agent details |
| `calling_cdr_outgoing` | calling_cdr | Outgoing calls with campaign info |
| `manual_outbound_calls` | calling_cdr | Manual outbound calls (call_mode=3) |
| `failed_calls` | calling_cdr | Failed/not patched calls |
| `abandoned_calls` | calling_cdr | Abandoned calls |
| `auto_call_distribution` | calling_cdr | Power/progressive/predictive dialer calls |
| `transfer_conference_calls` | calling_cdr | Transferred & conference calls |
| `callback_followup` | customer_followup | Callback/follow-up reminders |
| `list_wise_dialing_status` | calling_cdr | Dialing status by uploaded list |

**Default Parameters:**
- `start_date`: Current date 00:00:00
- `end_date`: Current date 23:59:59
- `sme_id`: 20002124
- `limit`: 1000

### 7.2 MariaDB Reports (config/mariadb_queries.json)

| Report Name | Tables | Description |
|-------------|--------|-------------|
| `agent_activity` | agent_details, agent_calling_details, log_history | Agent login times, durations, breaks |
| `agent_status_report` | agent_details, agent_calling_details | Real-time agent status |
| `sms_report` | smeReport | SMS triggered by agents |
| `whatsapp_report` | whatsAppReport | WhatsApp messages by agents |

---

## 8. AGENT SYSTEM DETAILS

### 8.1 Supervisor Agent

**Role:** Orchestrator and router

**Capabilities:**
- Routes queries to appropriate sub-agents
- Handles greetings and small talk directly
- Passes through responses unchanged
- Enforces JSON output format

**Routing Rules:**

| User Query About | Action |
|------------------|--------|
| Call logs, records, history | Delegate to data_extraction_agent |
| Reports, exports | Delegate to data_extraction_agent |
| Counts, metrics, statistics | Delegate to data_extraction_agent |
| Charts, visualizations | Delegate to visualisation_agent |
| Greetings, small talk | Handle directly |
| System explanations | Handle directly |

**Output Format:**
```json
{
  "summary": "Markdown-supported response text",
  "report_path": "path/to/file.xlsx or null",
  "chart_data": { "Chart.js config" }
}
```

### 8.2 Data Extraction Agent

**Role:** Database querying and report generation

**Available Tools:**

1. **MongoDB MCP Tools** (prefix: `mongodb__`)
   - Custom aggregation queries
   - Collection exploration

2. **MariaDB MCP Tools** (prefix: `mariadb__`)
   - Custom SQL queries
   - Schema discovery

3. **generate_reports** (MongoDB)
   - Predefined report execution
   - Excel file generation

4. **generate_mariadb_reports** (MariaDB)
   - Predefined SQL report execution
   - Excel file generation

**Tool Selection Priority:**
1. Predefined report → `generate_reports` / `generate_mariadb_reports`
2. Custom MongoDB → MongoDB MCP tools
3. Custom MariaDB → MariaDB MCP tools
4. Unclear source → Infer or ask user

### 8.3 Visualization Agent

**Role:** Chart.js configuration generation

**Supported Chart Types:**
- Bar charts
- Pie charts
- Line charts
- Doughnut charts
- Radar charts
- Scatter plots

**Output Format:**
```json
{
  "type": "bar | pie | line | doughnut | radar | scatter",
  "data": {
    "labels": [],
    "datasets": [{
      "label": "...",
      "data": [],
      "backgroundColor": [],
      "borderColor": [],
      "borderWidth": 1
    }]
  },
  "options": {
    "responsive": true,
    "plugins": {
      "legend": { "display": true, "position": "top" },
      "title": { "display": true, "text": "..." }
    }
  }
}
```

---

## 9. DATA FLOW DIAGRAMS

### 9.1 Query Processing Flow

```
User types message in chat
         │
         ▼
Frontend: ChatInput.tsx
- Validates input
- Creates user message object
- Adds to conversation
         │
         ▼
Frontend: useChatStore.sendQuery()
- Clears previous streaming state
- Resets thinking steps
- Sends WebSocket message
         │
         ▼
WebSocket: {type: "query", token, data: {message}}
         │
         ▼
Backend: websocket.py/handle_websocket()
- Validates token
- Creates ws_id if new connection
- Creates session folder
- Initializes agents with MCP tools
         │
         ▼
Backend: Supervisor Agent
- Analyzes query intent
- Decides: handle directly OR delegate
         │
         ├──────────────────────────────────┐
         ▼                                  ▼
Handle Directly                     Delegate to Data Agent
(greetings, etc.)                   (reports, queries)
         │                                  │
         │                                  ▼
         │                          Data Extraction Agent
         │                          - Selects appropriate tool
         │                          - Executes query
         │                          - Generates Excel if needed
         │                          - Returns JSON response
         │                                  │
         │                                  ▼
         │                          (Optional) Visualisation Agent
         │                          - Creates chart config
         │                                  │
         ◄──────────────────────────────────┘
         │
         ▼
Backend: websocket.py
- Streams events to frontend
- Transforms [DOWNLOAD:path] to full URL
- Sends final response
         │
         ▼
Frontend: ws-message-handler.ts
- Parses WebSocket messages
- Filters by type
- Stores in appropriate category
         │
         ▼
Frontend: chat-store-helpers.ts/handleWebSocketMessage()
- Updates thinkingSteps for "message" type
- Starts fake streaming for "final" type
- Adds assistant message to conversation on "complete"
         │
         ▼
Frontend: MessageList.tsx
- Displays thinking process
- Shows streaming content
- Renders markdown tables
- Shows download button
- Displays charts
```

### 9.2 Excel Generation Flow

```
Data Agent receives report request
         │
         ▼
generate_reports() / generate_mariadb_reports()
         │
         ▼
Load query config from JSON
- Get collection/table name
- Get aggregation pipeline/SQL query
- Apply date placeholders
         │
         ▼
Execute query via MCP or direct connection
         │
         ▼
Process results
- Format dates
- Flatten nested objects
- Remove _id fields
         │
         ▼
Create Excel file
- write_only=True for memory efficiency
- Add headers from first row
- Write all data rows
         │
         ▼
Save to: agent_files/sessions/{ws_id}/outputs/{filename}.xlsx
         │
         ▼
Return: [DOWNLOAD:outputs/filename.xlsx]
         │
         ▼
WebSocket transforms to: sessions/{ws_id}/outputs/filename.xlsx
         │
         ▼
Frontend shows download button
         │
         ▼
User clicks → GET /api/chat/download/sessions/{ws_id}/outputs/filename.xlsx
         │
         ▼
Backend serves file with send_file()
```

---

## 10. SECURITY MEASURES

### 10.1 Database Security
- **READ-ONLY mode** for all database connections
- MCP servers started with `--readOnly` flag
- No write/update/delete operations allowed

### 10.2 Authentication
- Token-based session management
- UUID tokens stored in memory
- Sessions cleared on logout
- Frontend persists auth state in localStorage

### 10.3 File Security
- Path traversal prevention in download endpoint
- Files only served from `agent_files/` directory
- Session isolation (each ws_id has separate folder)
- Session folders cleaned up on disconnect

### 10.4 Environment Security
- Secrets stored in `.env` (gitignored)
- `.env.example` provided without real credentials
- Connection strings not logged

### 10.5 Input Validation
- WebSocket messages validated for type and token
- Query content passed through AI agent (no direct SQL/NoSQL)

---

## 11. PERFORMANCE OPTIMIZATIONS

### 11.1 Backend Optimizations
- **MCP tools loaded once** at startup (not per request)
- **Session-based agents** reused within WebSocket connection
- **LangGraph MemorySaver** for conversation persistence
- **10ms event loop** for responsive streaming

### 11.2 Frontend Optimizations
- **Instant display** for long responses (>500 chars)
- **Word-by-word streaming** for short responses
- **Smart scroll** - auto-scroll only when near bottom
- **Version caching** for retry responses

### 11.3 Excel Generation Optimizations
- **write_only=True** mode for openpyxl
- Streaming writes (doesn't load entire file in memory)
- Efficient nested document flattening

---

## 12. ERROR HANDLING

### 12.1 Connection Errors

```python
# MCP connection error handling
if "connection refused" in error:
    retry_connection(max_retries=3)
```

### 12.2 Query Errors
- Empty results return: `{summary: "No records found", report_path: null}`
- Tool errors logged and returned to user
- WebSocket errors sent with `{type: "error", data: {message}}`

### 12.3 Frontend Error Handling
- Login errors displayed in form
- WebSocket reconnection on disconnect
- Export errors shown below download button

---

## 13. CONFIGURATION REFERENCE

### 13.1 Backend Environment (.env)

```env
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-mini
OPENAI_TEMPERATURE=0.3

# MongoDB MCP
MDB_MCP_CONNECTION_STRING=mongodb://user:pass@host:port/db?authMechanism=SCRAM-SHA-1
MDB_MCP_READ_ONLY=true
MONGODB_DATABASE=ccs_dev

# MariaDB
MYSQL_HOST=host
MYSQL_USER=user
MYSQL_PASS=password
MYSQL_DB_NAME=ccs_dev

# Langfuse (Optional)
ENABLE_LANGFUSE=true
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 13.2 Frontend Environment (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 13.3 MCP Configuration (config/mcp.json)

```json
{
  "servers": {
    "mongodb": {
      "transport": "streamable_http",
      "url": "http://127.0.0.1:4000/mcp"
    },
    "mariadb": {
      "transport": "streamable_http",
      "url": "http://127.0.0.1:9001/mcp"
    }
  }
}
```

---

## 14. STARTUP SEQUENCE

### Step 1: Start MongoDB MCP Server (Port 4000)

```powershell
$env:MDB_MCP_CONNECTION_STRING = "mongodb://..."
npx -y mongodb-mcp-server@1.2.0 --readOnly --transport http --httpPort 4000
```

### Step 2: Start MariaDB MCP Server (Port 9001)

```bash
# Separate terminal
# MariaDB MCP server setup (implementation-specific)
```

### Step 3: Start Backend (Port 8000)

```bash
python app.py
```

### Step 4: Start Frontend (Port 3000)

```bash
cd frontend && npm run dev
```

### Access Application

Navigate to: `http://localhost:3000`

---

## 15. FEATURES SUMMARY

### 15.1 Implemented Features

- [x] Real-time WebSocket chat with streaming
- [x] Multi-agent AI system (Supervisor, Data Extraction, Visualization)
- [x] MongoDB integration via MCP
- [x] MariaDB integration via MCP
- [x] 9 predefined MongoDB reports
- [x] 4 predefined MariaDB reports
- [x] Excel report generation
- [x] Chart.js visualization
- [x] Thought process display
- [x] Conversation memory
- [x] Session isolation
- [x] Authentication system
- [x] Collapsible sidebar
- [x] Smart scroll behavior
- [x] Response retry with versioning
- [x] Copy/feedback actions
- [x] Langfuse tracing (optional)

### 15.2 Future Enhancement Areas

- [ ] Multi-user threading
- [ ] PDF report generation
- [ ] Email delivery
- [ ] Voice input
- [ ] Mobile responsive improvements
- [ ] Real-time notifications

---

## 16. QUICK REFERENCE

### 16.1 Key Ports

| Service | Port |
|---------|------|
| Frontend | 3000 |
| Backend | 8000 |
| MongoDB MCP | 4000 |
| MariaDB MCP | 9001 |
| MongoDB | 27017 |

### 16.2 Key Directories

| Directory | Purpose |
|-----------|---------|
| `agents/` | AI agent implementations |
| `routes/` | Flask API endpoints |
| `tools/` | Agent tools (Excel, reports) |
| `prompts/` | System prompts for agents |
| `config/` | Configuration files |
| `agent_files/sessions/` | Generated Excel files |
| `frontend/src/components/chat/` | React chat components |
| `frontend/src/lib/` | State management & utilities |

### 16.3 Key Files

| File | Purpose |
|------|---------|
| `app.py` | Flask entry point |
| `agents/supervisor_agent.py` | Main orchestrator agent |
| `agents/data_extraction_agent.py` | Database query agent |
| `routes/websocket.py` | WebSocket handler |
| `tools/mongodb_query_tool.py` | MongoDB report tool |
| `config/queries.json` | Predefined MongoDB queries |
| `frontend/src/lib/chat-store.ts` | Chat state management |
| `frontend/src/lib/ws-message-handler.ts` | WebSocket message handler |

---

## 17. SAMPLE QUERIES

### 17.1 Call Reports

```
Give me incoming call report for today
Show me outgoing calls for yesterday
Generate missed call report
Get failed calls for this week
```

### 17.2 Agent Performance

```
How many calls did agent manas handle?
Show me agent activity report
Which agent handled the most calls?
```

### 17.3 Call Analytics

```
How many calls were made today?
Show me call duration statistics
Count failed calls for this week
```

### 17.4 Data Filtering

```
Show me calls from customer +916283921151
List all successful calls
Filter calls by agent ayushi
```

---

## 18. TROUBLESHOOTING

### 18.1 Common Issues

| Issue | Solution |
|-------|----------|
| MongoDB connection refused | Check MCP server is running on port 4000 |
| WebSocket disconnects | Check backend is running on port 8000 |
| Excel download fails | Check session folder exists in agent_files |
| Login fails | Verify credentials (demo/demo123) |
| Chart not displaying | Check chart_data format in response |

### 18.2 Debug Commands

```bash
# Check MongoDB MCP server
curl http://localhost:4000/mcp

# Check backend health
curl http://localhost:8000/api/auth/session

# Check frontend
curl http://localhost:3000
```

---

*Last Updated: December 2025*

*Document generated for Contact Center AI Agent System v1.0*
