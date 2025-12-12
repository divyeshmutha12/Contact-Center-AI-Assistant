# Contact Center AI Agent System

An AI-powered full-stack contact center analytics system with real-time chat, data querying, and Excel report generation.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  - Real-time WebSocket Chat                                  │
│  - Excel Report Downloads                                    │
│  - Authentication                                             │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/WebSocket
┌────────────────────▼────────────────────────────────────────┐
│                   Backend (Flask + Python)                   │
│  ┌──────────────┐      ┌─────────────────┐                 │
│  │  WebSocket   │      │   REST API      │                 │
│  │  Streaming   │      │   Auth/Download │                 │
│  └──────┬───────┘      └────────┬────────┘                 │
│         │                       │                            │
│  ┌──────▼───────────────────────▼────────┐                 │
│  │      Supervisor Agent (GPT-5-mini)    │                 │
│  │      - Routes queries                   │                 │
│  │      - Manages conversation             │                 │
│  └──────────────────┬─────────────────────┘                 │
│                     │                                         │
│  ┌──────────────────▼─────────────────────┐                 │
│  │   Data Extraction Agent (GPT-5-mini)  │                 │
│  │   - MongoDB queries via MCP             │                 │
│  │   - Excel report generation             │                 │
│  │   - Markdown table formatting           │                 │
│  └──────────────────┬─────────────────────┘                 │
└────────────────────┬┴──────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              MongoDB MCP Server (Node.js)                    │
│  - Provides standardized DB tools                            │
│  - Read-only mode for safety                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 MongoDB Database (ccs_dev)                   │
│  - calling_cdr collection (call records)                     │
│  - address_book collection (customers)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

### Required Software

1. **Python 3.11+**
   - Download: https://www.python.org/downloads/
   - Verify: `python --version`

2. **Node.js 20.19.0+**
   - Download: https://nodejs.org/
   - Verify: `node --version` and `npm --version`

3. **MongoDB**
   - Running on: `10.144.61.67:27017` (remote server)
   - Database: `ccs_dev`
   - Authentication: SCRAM-SHA-1

4. **OpenAI API Key**
   - Get from: https://platform.openai.com/api-keys
   - Model used: `gpt-5-mini`

---

## 🚀 Installation Guide

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Contact_Center_Project
```

### Step 2: Backend Setup

#### 2.1 Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 2.2 Configure Backend Environment

Copy the example file and create `.env`:

```bash
# Windows PowerShell
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Edit `.env` file with your credentials:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-5-mini
OPENAI_TEMPERATURE=0.3

# MongoDB MCP Server config (used by MCP server)
MDB_MCP_CONNECTION_STRING=mongodb://Ayushi:Ayushi%40123@10.144.61.67:27017/ccs_dev?authMechanism=SCRAM-SHA-1
MDB_MCP_READ_ONLY=true
MONGODB_DATABASE=ccs_dev

# Langfuse Tracing Configuration (Optional)
ENABLE_LANGFUSE=true
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Important Notes:**
- Replace `OPENAI_API_KEY` with your actual OpenAI API key
- The MongoDB connection string includes URL-encoded password (`%40` = `@`)
- Langfuse is optional for tracing/observability

### Step 3: Frontend Setup

#### 3.1 Navigate to Frontend Directory

```bash
cd frontend
```

#### 3.2 Install Node Dependencies

```bash
npm install
```

#### 3.3 Configure Frontend Environment

Create `frontend/.env.local`:

```env
# Backend API Configuration
# HTTP/REST endpoints (auth, download)
NEXT_PUBLIC_API_URL=http://localhost:8000

# WebSocket endpoint (chat, streaming)
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## 🎯 Running the System

### Terminal 1: Start MongoDB MCP Server

**Windows PowerShell:**
```powershell
$env:MDB_MCP_CONNECTION_STRING = "mongodb://Ayushi:Ayushi%40123@10.144.61.67:27017/ccs_dev?authMechanism=SCRAM-SHA-1"
npx -y mongodb-mcp-server@1.2.0 --readOnly --transport http --httpPort 4000
```

**Mac/Linux:**
```bash
export MDB_MCP_CONNECTION_STRING="mongodb://Ayushi:Ayushi%40123@10.144.61.67:27017/ccs_dev?authMechanism=SCRAM-SHA-1"
npx -y mongodb-mcp-server@1.2.0 --readOnly --transport http --httpPort 4000
```

You should see:
```
MongoDB MCP Server running on http://localhost:4000
```

### Terminal 2: Start Backend Server

```bash
# From project root
python app.py
```

You should see:
```
Server running at: http://localhost:8000
```

### Terminal 3: Start Frontend

```bash
# From frontend directory
cd frontend
npm run dev
```

You should see:
```
- Local: http://localhost:3000
```

### Access the Application

Open your browser and navigate to: **http://localhost:3000**

---

## 💬 Using the Chat Interface

### Sample Queries

#### Call Reports
```
Give me incoming call report for today
Show me outgoing calls for yesterday
Generate missed call report
```

#### Agent Performance
```
How many calls did agent manas handle?
Show me agent performance report
Which agent handled the most calls?
```

#### Call Analytics
```
How many calls were made today?
Show me call duration statistics
Count failed calls for this week
```

#### Data Filtering
```
Show me calls from customer +916283921151
List all successful calls
Filter calls by agent ayushi
```

### Features

1. **Real-time Streaming**: AI responses stream word-by-word
2. **Thinking Steps**: See AI reasoning process
3. **Markdown Tables**: Data displayed in formatted tables
4. **Excel Downloads**: Click "Download Excel Report" button to get full data
5. **Conversation Memory**: Context maintained across messages

---

## 📊 Excel Report Generation

### How It Works

1. User requests a report (e.g., "Give me incoming call report")
2. AI queries MongoDB and gets data
3. AI generates Excel file in session folder
4. AI returns:
   - Preview table (first 10 rows) in chat
   - Download button with file path
5. User clicks download button
6. Excel file downloaded with all records

### Download Endpoint

```
GET /api/chat/download/sessions/{ws_id}/outputs/{filename}.xlsx
```

Example:
```
GET http://localhost:8000/api/chat/download/sessions/ws_abc123/outputs/incoming_calls_report.xlsx
```

### File Location

```
agent_files/
└── sessions/
    └── ws_abc123/           # Session ID
        └── outputs/
            └── report.xlsx   # Generated Excel files
```

---

## 🔧 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Authentication

**POST** `/api/auth/login`
```json
{
  "username": "demo",
  "password": "demo123"
}
```

Response:
```json
{
  "token": "uuid-token",
  "username": "demo",
  "status": "success"
}
```

**POST** `/api/auth/logout`
```json
{
  "token": "your-token"
}
```

#### 2. WebSocket Chat

**WebSocket** `/ws/chat`

Connect and send:
```json
{
  "type": "query",
  "token": "your-token",
  "data": {
    "message": "How many calls today?"
  }
}
```

Receive events:
- `connection` - Connection established with ws_id
- `query_received` - Query acknowledged
- `message` - AI thinking/reasoning
- `tool_start` - Tool execution started
- `tool_end` - Tool execution completed
- `final` - Final response with summary and report_path
- `complete` - Response processing complete

#### 3. File Download

**GET** `/api/chat/download/{path}`

Example:
```
GET /api/chat/download/sessions/ws_abc123/outputs/report.xlsx
```

---

## 📁 Project Structure

```
Contact_Center_Project/
├── agents/
│   ├── __init__.py
│   ├── supervisor_agent.py          # Supervisor agent (routes queries)
│   ├── data_extraction_agent.py     # Data extraction agent (MongoDB)
│   └── mongo_mcp_client.py          # MCP client initialization
├── routes/
│   ├── __init__.py
│   ├── auth.py                      # Authentication endpoints
│   ├── chat.py                      # Chat & download endpoints
│   └── websocket.py                 # WebSocket handler
├── prompts/
│   ├── supervisor_system.txt        # Supervisor agent prompt
│   └── data_agent_system.txt        # Data extraction agent prompt
├── tools/
│   └── excel_converter.py           # EJSON to Excel converter
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── login/page.tsx       # Login page
│   │   │   └── chat/page.tsx        # Chat interface
│   │   ├── components/
│   │   │   └── chat/                # Chat UI components
│   │   └── lib/
│   │       ├── auth-store.ts        # Authentication state
│   │       ├── chat-store.ts        # Chat state management
│   │       └── ws-message-handler.ts # WebSocket handler
│   ├── public/
│   └── package.json
├── config/
│   └── mcp.json                     # MCP server configuration
├── agent_files/
│   └── sessions/                    # Session-specific files
│       └── {ws_id}/
│           └── outputs/             # Generated Excel reports
├── .env                             # Backend environment (not in git)
├── .env.example                     # Environment template
├── .gitignore
├── requirements.txt                 # Python dependencies
├── app.py                          # Flask application
└── README.md                        # This file
```

---

## 🔍 Features

### ✅ Implemented

- [x] Real-time WebSocket chat
- [x] AI-powered query routing
- [x] MongoDB data extraction via MCP
- [x] Excel report generation
- [x] Markdown table rendering
- [x] File download with session isolation
- [x] Authentication (token-based)
- [x] Conversation memory
- [x] Thinking/reasoning display
- [x] Langfuse tracing integration
- [x] Session-based file management
- [x] Automatic summarization (long conversations)

### 🔮 Future Enhancements

- [ ] Multi-user conversation threading
- [ ] Chart/graph generation from data
- [ ] PDF report generation
- [ ] Email report delivery
- [ ] Advanced filtering UI
- [ ] Real-time notifications
- [ ] Voice input support
- [ ] Mobile responsive design improvements

---

## 📚 Technology Stack

### Backend
- **Python 3.11**
- **Flask** - Web framework
- **Flask-Sock** - WebSocket support
- **LangChain** - AI agent framework
- **LangGraph** - Agent orchestration
- **OpenAI GPT-5-mini** - Language model
- **MongoDB MCP Server** - Database integration
- **Langfuse** - Tracing & observability
- **openpyxl** - Excel generation

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Zustand** - State management
- **TailwindCSS** - Styling
- **ReactMarkdown** - Markdown rendering
- **remark-gfm** - GitHub Flavored Markdown

### Database
- **MongoDB 7.0+** - NoSQL database
- **Collections**: calling_cdr, address_book

---

## 📖 Additional Resources

### Documentation Links
- OpenAI API: https://platform.openai.com/docs
- LangChain: https://python.langchain.com/docs
- MongoDB MCP Server: https://github.com/mongodb/mongodb-mcp-server
- Next.js: https://nextjs.org/docs
- Langfuse: https://langfuse.com/docs

### Key Concepts

**WebSocket Flow:**
```
Client connects → Server assigns ws_id → Client sends query →
Server streams thinking/reasoning → Server sends final response →
Client displays table + download button
```

**Session Management:**
```
Each WebSocket connection = Unique ws_id = Isolated file system
Files stored in: agent_files/sessions/{ws_id}/outputs/
```

**Report Generation:**
```
MongoDB query → EJSON result → convert_ejson_to_excel tool →
Excel file created → Path returned → Download button shown
```

---

## 👥 Team & Support

For questions or issues:
1. Check this README
2. Review error logs in terminal
3. Check Langfuse traces (if enabled)
4. Contact the development team

---

## 📄 License

Internal use only - Contact Center Analytics System
