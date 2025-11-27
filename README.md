# Contact Center Agent System

An AI-powered agent system for querying and analyzing contact center data using MongoDB MCP Server, LangGraph, and OpenAI GPT-5-mini.

## Architecture

```
User Query (CLI or REST API)
    ↓
Flask API (app.py) ─── or ─── CLI (main.py)
    ↓
Supervisor Agent (LangGraph + GPT-5-mini)
    ↓
Data Extraction Agent
    ↓
MongoDB MCP Server (port 4000)
    ↓
MongoDB Database (ccs_dev)
```

## Components

### 1. **Supervisor Agent**
- Built using LangChain's `create_agent` pattern
- Uses OpenAI GPT-5-mini for natural language understanding
- Automatic tool calling and routing
- Routes DB queries to Data Extraction Agent

### 2. **Data Extraction Agent**
- Primary: Connects to MongoDB via MCP Server
- Fallback: Direct PyMongo connection
- Handles queries, aggregations, and data retrieval
- Circuit breaker pattern for reliability

### 3. **MongoDB MCP Server**
- Official MongoDB MCP Server (stdio transport)
- Provides standardized tools for database operations
- Read-only mode for data safety

## Prerequisites

### Required Software

1. **Python 3.8+**
   - Download: https://www.python.org/downloads/

2. **Node.js 20.19.0+**
   - Download: https://nodejs.org/
   - Required for MongoDB MCP Server

3. **MongoDB Community Edition**
   - Download: https://www.mongodb.com/try/download/community
   - Must be running locally on port 27017

4. **OpenAI API Key**
   - Get one from: https://platform.openai.com/api-keys

### Optional Tools

- **MongoDB Compass** (GUI for MongoDB)
  - Download: https://www.mongodb.com/try/download/compass

## Installation

### Step 1: Clone/Download the Project

```bash
cd Contact_Center_Project
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Install MongoDB MCP Server (via NPM)

```bash
npm install -g mongodb-mcp-server
```

Or it will be installed automatically via NPX when running the system.

### Step 4: Configure Environment Variables

1. Copy the example env file:
```bash
copy .env.example .env
```

2. Edit `.env` and add your OpenAI API key and model:
```
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-5-mini
OPENAI_TEMPERATURE=0.3
MDB_MCP_CONNECTION_STRING=mongodb://localhost:27017/ccs_dev
MDB_MCP_READ_ONLY=true
MONGODB_DATABASE=ccs_dev
```

### Step 5: Start MongoDB

Make sure MongoDB is running:

**Windows:**
```bash
net start MongoDB
```

**Mac/Linux:**
```bash
brew services start mongodb-community
# or
sudo systemctl start mongod
```

### Step 6: Generate Mock Data

```bash
python data/generate_mock_data.py
```

This will:
- Generate sample call records
- Create the `ccs_dev` database
- Create collections for calls, agents, customers
- Insert sample data
- Create indexes for better performance

## Usage

### Option 1: Run CLI Agent (Interactive)

```bash
python main.py
```

### Option 2: Run REST API Server

```bash
python app.py
```

This starts the Flask API server at `http://localhost:8000`

---

## REST API Documentation

### Prerequisites for API

Before starting the API server, ensure:
1. MongoDB is running on `localhost:27017`
2. MCP Server is running:
   ```bash
   npx -y mongodb-mcp-server --connectionString "mongodb://localhost:27017/ccs_dev" --readOnly --port 4000
   ```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info and available endpoints |
| POST | `/auth/login` | Login and get auth token |
| POST | `/auth/logout` | Logout and invalidate token |
| POST | `/auth/session` | Get session info |
| POST | `/chat/` | Send message to AI agent |
| GET | `/chat/health` | Health check |

### Authentication Flow

#### 1. Login
```bash
POST /auth/login
Content-Type: application/json

{
    "username": "demo",
    "password": "demo123"
}
```

Response:
```json
{
    "token": "uuid-token-here",
    "username": "demo",
    "status": "success"
}
```

#### 2. Chat with Agent
```bash
POST /chat/
Content-Type: application/json

{
    "token": "your-token-here",
    "message": "How many calls were made today?"
}
```

Response:
```json
{
    "reply": "There are 821 calls recorded today.",
    "status": "success"
}
```

#### 3. Logout
```bash
POST /auth/logout
Content-Type: application/json

{
    "token": "your-token-here"
}
```

### Testing with Postman

1. **Login**: POST to `http://localhost:8000/auth/login` with username/password
2. **Copy the token** from response
3. **Chat**: POST to `http://localhost:8000/chat/` with token and message
4. **Logout**: POST to `http://localhost:8000/auth/logout` with token

### Sample Queries

| Query Type | Example |
|------------|---------|
| Count | "How many calls were made today?" |
| Filter | "Show me calls for agent manas" |
| List | "List all failed calls" |
| General | "What is a contact center?" |

---

### Example Queries

Once the system starts, you can ask natural language queries:

```
👤 You: Find all customers from New York

👤 You: Show me VIP customers

👤 You: How many customers joined in 2024?

👤 You: What is the distribution of customers by status?

👤 You: List customers with more than 5 interactions

👤 You: Show customers from California with active status
```

### Available Commands

- **help** or **?** - Show help information
- **examples** - Display example queries
- **status** - Check system status
- **quit** or **exit** - Exit the program

## Project Structure

```
Contact_Center_Project/
├── agents/
│   ├── __init__.py
│   ├── supervisor_agent.py        # LangGraph supervisor with GPT-5-mini
│   ├── data_extraction_agent.py   # Data extraction agent
│   └── mongo_mcp_client.py        # MongoDB MCP client wrapper
├── routes/
│   ├── __init__.py
│   ├── auth.py                    # Authentication endpoints
│   └── chat.py                    # Chat endpoints
├── config/
│   └── mcp_servers.json           # MCP server configuration
├── data/
│   ├── generate_mock_data.py      # Mock data generator
│   └── sample_customers.json      # Generated sample data
├── .env.example                    # Environment variables template
├── .env                            # Your actual API keys (not in git)
├── requirements.txt                # Python dependencies
├── main.py                         # CLI entry point
├── app.py                          # Flask REST API server
└── README.md                       # This file
```

## How It Works

### 1. Query Processing Flow

```
User enters query (via CLI or REST API)
    ↓
Supervisor Agent analyzes intent using GPT-5-mini
    ↓
Determines if it's a DB query or general question
    ↓
Routes to Data Extraction Agent (if DB query)
    ↓
Data Extraction Agent queries MongoDB via MCP
    ↓
Results returned to Supervisor
    ↓
Supervisor formats response with GPT-5-mini
    ↓
Final response returned to user
```

### 2. MCP Connection with Fallback

```
Data Extraction Agent
    ↓
[Try] Connect to MongoDB MCP Server (stdio)
    ↓
[Success] → Use MCP tools (find, aggregate, etc.)
    ↓
[Failure] → Fallback to direct PyMongo connection
    ↓
Execute query and return results
```

### 3. Agent Workflow (LangGraph)

```
┌─────────────┐
│ Supervisor  │ ← Entry point
└──────┬──────┘
       │
       ├──→ [Task = Query/Aggregate]
       │         ↓
       │    ┌─────────────────┐
       │    │ Data Extraction │
       │    └────────┬────────┘
       │             │
       ├──→ [Task = Analyze]
       │         ↓
       │    ┌──────────┐
       └───→│ Analysis │
            └────┬─────┘
                 │
            ┌────▼─────┐
            │Synthesize│
            └────┬─────┘
                 │
                END
```

## Database Schema

### Customers Collection

```json
{
  "customer_id": "CUST-00001",
  "name": "John Smith",
  "email": "john.smith@email.com",
  "phone": "+1-555-123-4567",
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip": "10001"
  },
  "customer_since": "2023-05-15T10:30:00",
  "status": "active",
  "interaction_count": 5,
  "interaction_history": [
    {
      "date": "2024-01-15T14:30:00",
      "type": "call",
      "duration_minutes": 15,
      "resolved": true,
      "notes": "Customer contacted regarding billing"
    }
  ],
  "lifetime_value": 2500.50,
  "notes": "Customer preferred contact: email"
}
```

### Indexed Fields

- `customer_id` (unique)
- `email`
- `status`
- `address.city`
- `address.state`

## MongoDB MCP Server Tools

The official MongoDB MCP Server provides these tools:

- **find** - Query documents with filters
- **aggregate** - Run aggregation pipelines
- **count** - Count documents
- **collection-schema** - Inspect collection schema
- **list-collections** - List all collections
- **db-stats** - Database statistics

## Troubleshooting

### MongoDB Connection Issues

**Error:** `Failed to connect to MongoDB`

**Solutions:**
1. Make sure MongoDB is running:
   ```bash
   # Windows
   net start MongoDB

   # Mac
   brew services start mongodb-community
   ```

2. Check MongoDB is listening on port 27017:
   ```bash
   netstat -an | findstr 27017
   ```

3. Verify connection string in `.env`:
   ```
   MDB_MCP_CONNECTION_STRING=mongodb://localhost:27017/ccs_dev
   ```

### MCP Server Issues

**Error:** `Failed to connect to MCP Server`

**Solutions:**
1. Ensure Node.js is installed:
   ```bash
   node --version
   ```

2. Install MongoDB MCP Server:
   ```bash
   npm install -g mongodb-mcp-server
   ```

3. The system will automatically fall back to direct PyMongo connection

### OpenAI API Issues

**Error:** `OPENAI_API_KEY not found`

**Solutions:**
1. Create `.env` file in project root
2. Add your API key:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```

3. Verify the key is valid at https://platform.openai.com/api-keys

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'langgraph'`

**Solution:**
```bash
pip install -r requirements.txt
```

## Testing the Flow

### Test 1: Data Extraction Agent Only

```bash
python agents/data_extraction_agent.py
```

This tests:
- MCP server connection
- MongoDB queries
- Fallback mechanism

### Test 2: Supervisor Agent

```bash
python agents/supervisor_agent.py
```

This tests:
- LangGraph workflow
- OpenAI GPT-5-mini integration
- Full agent orchestration

### Test 3: Full System

```bash
python main.py
```

Test with queries like:
- "Find customers from New York"
- "How many VIP customers?"
- "Show customer status distribution"

## Configuration

### Environment Variables

All configuration is managed through the `.env` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-5-mini
OPENAI_TEMPERATURE=0.3

# MongoDB MCP Server config
MDB_MCP_CONNECTION_STRING=mongodb://localhost:27017/ccs_dev
MDB_MCP_READ_ONLY=true
MONGODB_DATABASE=ccs_dev
```

**Benefits of configuration via .env:**
- No code changes needed to switch models
- Easy to use different settings per environment
- Keep secrets out of code
- Follow industry best practices

### MCP Server Configuration

Edit `config/mcp_servers.json`:

```json
{
  "servers": {
    "mongodb": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "mongodb-mcp-server@latest", "--readOnly"],
      "env": {
        "MDB_MCP_CONNECTION_STRING": "mongodb://localhost:27017/ccs_dev"
      }
    }
  }
}
```

### Enable Write Operations

To allow data modifications (not recommended for testing):

1. Remove `--readOnly` from `args` in `mcp_servers.json`
2. Set environment variable:
   ```
   MDB_MCP_READ_ONLY=false
   ```

## Next Steps

### Phase 1: Core System ✅
- Supervisor Agent
- Data Extraction Agent
- MongoDB MCP integration
- Backend CLI testing

### Phase 2: REST API ✅
- [x] Flask REST API server
- [x] Token-based authentication
- [x] Chat endpoint with AI agent
- [x] Health check endpoint
- [x] CORS enabled for frontend integration

### Phase 3: Future Enhancements
- [ ] Add conversation memory (multi-turn chat)
- [ ] Create web-based frontend
- [ ] Add more specialized agents (Analytics Agent, Report Agent)
- [ ] Implement caching for frequent queries
- [ ] Add real-time notifications (WebSocket)
- [ ] Add data visualization

## Contributing

This is an internal contact center project. For questions or issues, contact the development team.

## License

Internal use only.

## Support

For help or issues:
1. Check the troubleshooting section
2. Review MongoDB and MCP server logs
3. Verify all prerequisites are installed
4. Contact the development team

---

**Built with:**
- OpenAI GPT-5-mini
- MongoDB MCP Server
- LangGraph + LangChain
- Flask REST API
- Python 3.8+
- Node.js 20+
