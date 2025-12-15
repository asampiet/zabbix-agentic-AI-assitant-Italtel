# Network Troubleshooting Chat Assistant - Design Specification

## Document Information
| Field | Value |
|-------|-------|
| Version | 1.0 |
| Date | 2024-12-15 |
| Status | Draft |
| Related | detailed_requirements.md, functional_specification.md |

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Docker Host                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Host Network Mode                             │   │
│  │                                                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │   │
│  │  │   Frontend   │  │   Backend    │  │     MCP Server       │  │   │
│  │  │   (Node.js)  │  │  (FastAPI)   │  │      (Flask)         │  │   │
│  │  │   :13000     │  │   :13001     │  │      :13002          │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │   │
│  │         │                 │                    │                │   │
│  │         │                 │                    │                │   │
│  │         │          ┌──────┴──────┐            │                │   │
│  │         │          │             │            │                │   │
│  │  ┌──────┴──────┐  ┌▼────────────┐│  ┌────────▼───────────┐   │   │
│  │  │  PostgreSQL │  │   Strands   ││  │  Zabbix Instances  │   │   │
│  │  │   :13432    │  │   Agent     ││  │  (External)        │   │   │
│  │  │  + pgAdmin  │  │  (Bedrock)  ││  └────────────────────┘   │   │
│  │  │   :13050    │  └─────────────┘│                            │   │
│  │  └─────────────┘                 │                            │   │
│  │                                  │                            │   │
│  └──────────────────────────────────┴────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Service Responsibilities

| Service | Port | Responsibility |
|---------|------|----------------|
| Frontend | 13000 | React UI, Node.js server |
| Backend | 13001 | REST API, Strands Agent, Business Logic |
| MCP Server | 13002 | Zabbix API integration, Tool execution |
| PostgreSQL (App) | 13432 | Investigation history, Configuration |
| pgAdmin | 13050 | Database administration UI |
| Zabbix Web UI | 13080 | Zabbix monitoring web interface |
| Zabbix Server | 13051 | Zabbix server (agent connections) |
| Zabbix PostgreSQL | 13500 | Zabbix database |

### 1.3 AWS-Ready Design Considerations

| Local (Docker) | AWS Equivalent |
|----------------|----------------|
| Docker Compose | EKS (Kubernetes) |
| PostgreSQL container | Amazon RDS PostgreSQL |
| Environment variables | AWS Secrets Manager |
| Local filesystem (runbooks) | Amazon S3 / EFS |
| stdout logging | CloudWatch Logs |
| Host network | VPC + ALB |

---

## 2. Service Design

### 2.1 Frontend Service

**Technology Stack:**
- React 18 + TypeScript
- Zustand (state management)
- Material-UI (MUI) v5
- Vite (build tool)
- Node.js server (for potential SSR)

**Directory Structure:**
```
frontend/
├── Dockerfile
├── package.json
├── vite.config.ts
├── tsconfig.json
├── server.js              # Node.js server
├── public/
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── components/
    │   ├── Layout/
    │   │   ├── Header.tsx
    │   │   ├── MainLayout.tsx
    │   │   └── ConnectionStatusBar.tsx
    │   ├── Dashboard/
    │   │   ├── InstanceCard.tsx
    │   │   └── InstanceDetailModal.tsx
    │   ├── Alarms/
    │   │   ├── AlarmTable.tsx
    │   │   ├── AlarmFilters.tsx
    │   │   └── HostDetailModal.tsx
    │   ├── Chat/
    │   │   ├── ChatInterface.tsx
    │   │   ├── MessageList.tsx
    │   │   ├── MessageInput.tsx
    │   │   └── RunbookPanel.tsx
    │   └── History/
    │       ├── HistoryList.tsx
    │       └── HistoryDetail.tsx
    ├── stores/
    │   ├── instanceStore.ts
    │   ├── alarmStore.ts
    │   ├── chatStore.ts
    │   └── historyStore.ts
    ├── services/
    │   ├── api.ts
    │   └── polling.ts
    ├── types/
    │   └── index.ts
    └── theme/
        └── darkTheme.ts
```

**Zustand Store Example:**
```typescript
// stores/alarmStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AlarmState {
  alarms: Alarm[]
  filters: AlarmFilters
  lastPollTime: Date | null
  setAlarms: (alarms: Alarm[]) => void
  setFilters: (filters: AlarmFilters) => void
  clearFilters: () => void
}

export const useAlarmStore = create<AlarmState>()(
  persist(
    (set) => ({
      alarms: [],
      filters: { severities: [], instances: [], acknowledged: null },
      lastPollTime: null,
      setAlarms: (alarms) => set({ alarms, lastPollTime: new Date() }),
      setFilters: (filters) => set({ filters }),
      clearFilters: () => set({ filters: { severities: [], instances: [], acknowledged: null } }),
    }),
    { name: 'alarm-filters' }
  )
)
```

### 2.2 Backend Service

**Technology Stack:**
- Python 3.11+
- FastAPI
- Strands Agents SDK
- SQLAlchemy + asyncpg
- Pydantic v2

**Directory Structure:**
```
backend/
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── config/
│   ├── app.yaml
│   └── instances.yaml
├── runbooks/
│   ├── by-trigger/
│   ├── by-service/
│   └── general/
└── src/
    ├── main.py
    ├── config.py
    ├── api/
    │   ├── __init__.py
    │   ├── routes/
    │   │   ├── instances.py
    │   │   ├── alarms.py
    │   │   ├── chat.py
    │   │   ├── history.py
    │   │   └── runbooks.py
    │   └── dependencies.py
    ├── services/
    │   ├── __init__.py
    │   ├── mcp_client.py
    │   ├── agent_service.py
    │   ├── alarm_aggregator.py
    │   └── runbook_service.py
    ├── models/
    │   ├── __init__.py
    │   ├── database.py
    │   ├── investigation.py
    │   └── schemas.py
    └── agent/
        ├── __init__.py
        ├── network_agent.py
        └── prompts.py
```

**Strands Agent Integration:**
```python
# src/agent/network_agent.py
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
import httpx

class NetworkTroubleshootAgent:
    def __init__(self, mcp_base_url: str):
        self.mcp_base_url = mcp_base_url
        self.model = BedrockModel(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            temperature=0.3,
            streaming=True
        )
        self.agent = None
    
    async def initialize(self):
        """Initialize agent with MCP tools via HTTP."""
        tools = await self._load_mcp_tools()
        self.agent = Agent(
            model=self.model,
            tools=tools,
            system_prompt=NETWORK_ENGINEER_PROMPT
        )
    
    async def _load_mcp_tools(self) -> list:
        """Load tools from MCP server via HTTP."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.mcp_base_url}/tools")
            tool_definitions = response.json()
        return [self._create_http_tool(t) for t in tool_definitions]
    
    def _create_http_tool(self, tool_def: dict):
        """Create callable tool that invokes MCP server via HTTP."""
        @tool
        async def mcp_tool(**kwargs):
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mcp_base_url}/tools/{tool_def['name']}/invoke",
                    json={"instance_id": kwargs.pop("instance_id"), "params": kwargs}
                )
                return response.json()
        mcp_tool.__name__ = tool_def["name"]
        mcp_tool.__doc__ = tool_def["description"]
        return mcp_tool
    
    async def investigate(self, alarm: dict, instance_id: str) -> AsyncGenerator:
        """Run investigation and yield streaming response."""
        context = await self._build_context(alarm, instance_id)
        prompt = f"""Investigate this alarm:
        
Alarm: {alarm['description']}
Host: {alarm['host']}
Severity: {alarm['severity']}
Duration: {alarm['duration']}

Context:
{context}

Analyze the issue and provide:
1. Root cause analysis
2. Recommended actions
3. Relevant runbook steps
"""
        async for chunk in self.agent.stream(prompt):
            yield chunk
```

### 2.3 MCP Server Service

**Technology Stack:**
- Python 3.11+
- Flask
- python-zabbix-utils
- Gunicorn

**Directory Structure:**
```
mcp-server/
├── Dockerfile
├── requirements.txt
└── src/
    ├── main.py
    ├── config.py
    ├── tools/
    │   ├── __init__.py
    │   ├── host_tools.py
    │   ├── problem_tools.py
    │   ├── trigger_tools.py
    │   ├── template_tools.py
    │   ├── maintenance_tools.py
    │   └── config_tools.py
    └── zabbix/
        ├── __init__.py
        ├── client.py
        └── instance_manager.py
```

**Flask MCP Server:**
```python
# src/main.py
from flask import Flask, jsonify, request
from zabbix.instance_manager import InstanceManager

app = Flask(__name__)
instance_manager = InstanceManager()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

@app.route('/tools', methods=['GET'])
def list_tools():
    """Return all available MCP tools."""
    return jsonify(TOOL_DEFINITIONS)

@app.route('/tools/<tool_name>/invoke', methods=['POST'])
def invoke_tool(tool_name: str):
    """Invoke a specific tool."""
    data = request.json
    instance_id = data.get('instance_id')
    params = data.get('params', {})
    
    client = instance_manager.get_client(instance_id)
    result = TOOL_HANDLERS[tool_name](client, **params)
    return jsonify(result)

@app.route('/instances', methods=['GET'])
def list_instances():
    """Return all configured instances with status."""
    return jsonify(instance_manager.get_all_status())

@app.route('/instances/<instance_id>/status', methods=['GET'])
def instance_status(instance_id: str):
    """Check specific instance connectivity."""
    status = instance_manager.check_connection(instance_id)
    return jsonify(status)
```

**Zabbix Instance Manager:**
```python
# src/zabbix/instance_manager.py
from zabbix_utils import ZabbixAPI
from config import load_instances_config

class InstanceManager:
    def __init__(self):
        self.config = load_instances_config()
        self.clients: dict[str, ZabbixAPI] = {}
    
    def get_client(self, instance_id: str) -> ZabbixAPI:
        if instance_id not in self.clients:
            instance = self.config[instance_id]
            client = ZabbixAPI(url=instance['url'])
            client.login(user=instance['username'], password=instance['password'])
            self.clients[instance_id] = client
        return self.clients[instance_id]
    
    def check_connection(self, instance_id: str) -> dict:
        try:
            client = self.get_client(instance_id)
            version = client.api_version()
            return {"status": "connected", "version": version}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_all_status(self) -> list:
        return [
            {"id": iid, **self.check_connection(iid)}
            for iid in self.config.keys()
        ]
```


---

## 3. Database Design

### 3.1 PostgreSQL Schema

```sql
-- Investigations table
CREATE TABLE investigations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    
    -- Alarm context
    alarm_id VARCHAR(100) NOT NULL,
    alarm_description TEXT NOT NULL,
    alarm_severity VARCHAR(20) NOT NULL,
    host_name VARCHAR(255) NOT NULL,
    instance_id VARCHAR(100) NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Chat messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID REFERENCES investigations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Tool calls table (audit trail)
CREATE TABLE tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID REFERENCES investigations(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    parameters JSONB,
    result JSONB,
    duration_ms INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_investigations_started_at ON investigations(started_at DESC);
CREATE INDEX idx_investigations_instance_id ON investigations(instance_id);
CREATE INDEX idx_investigations_status ON investigations(status);
CREATE INDEX idx_chat_messages_investigation ON chat_messages(investigation_id);
CREATE INDEX idx_tool_calls_investigation ON tool_calls(investigation_id);

-- Full-text search index
CREATE INDEX idx_chat_messages_content_fts ON chat_messages 
    USING gin(to_tsvector('english', content));
```

### 3.2 SQLAlchemy Models

```python
# src/models/investigation.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base

class Investigation(Base):
    __tablename__ = "investigations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="in_progress")
    
    alarm_id = Column(String(100), nullable=False)
    alarm_description = Column(Text, nullable=False)
    alarm_severity = Column(String(20), nullable=False)
    host_name = Column(String(255), nullable=False)
    instance_id = Column(String(100), nullable=False)
    
    messages = relationship("ChatMessage", back_populates="investigation")
    tool_calls = relationship("ToolCall", back_populates="investigation")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.id"))
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    investigation = relationship("Investigation", back_populates="messages")

class ToolCall(Base):
    __tablename__ = "tool_calls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.id"))
    tool_name = Column(String(100), nullable=False)
    parameters = Column(JSONB)
    result = Column(JSONB)
    duration_ms = Column(Integer)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    investigation = relationship("Investigation", back_populates="tool_calls")
```

---

## 4. API Design

### 4.1 REST API Endpoints

#### Instances API
```yaml
GET /api/instances:
  description: List all configured Zabbix instances
  response:
    - id: string
      name: string
      status: connected | disconnected | error
      version: string
      problem_counts:
        disaster: number
        high: number
        average: number
        warning: number
        information: number
      last_sync: datetime

GET /api/instances/{id}/status:
  description: Get detailed status for specific instance
  response:
    id: string
    status: connected | disconnected | error
    version: string
    hosts_count: number
    error: string (if status=error)
```

#### Alarms API
```yaml
GET /api/alarms:
  description: Get aggregated alarms from all instances
  query_params:
    instance_id: string (optional, filter by instance)
    severity: string[] (optional, filter by severity)
    acknowledged: boolean (optional)
    host: string (optional, text search)
  response:
    alarms:
      - id: string
        instance_id: string
        instance_name: string
        host: string
        description: string
        severity: string
        severity_code: number
        duration: string
        acknowledged: boolean
        event_id: string
    last_poll: datetime

POST /api/alarms/{id}/acknowledge:
  description: Acknowledge an alarm
  body:
    instance_id: string
  response:
    success: boolean
    message: string
```

#### Chat API
```yaml
POST /api/chat/investigate:
  description: Start investigation for an alarm
  body:
    alarm_id: string
    instance_id: string
  response:
    investigation_id: string
    stream: true (SSE stream of agent responses)

POST /api/chat/message:
  description: Send message in current investigation
  body:
    investigation_id: string
    message: string
  response:
    stream: true (SSE stream)

GET /api/chat/history/{investigation_id}:
  description: Get chat history for investigation
  response:
    messages:
      - role: string
        content: string
        timestamp: datetime
```

#### History API
```yaml
GET /api/history:
  description: List investigation history
  query_params:
    page: number
    limit: number
    search: string (full-text search)
    instance_id: string
    severity: string[]
    from_date: datetime
    to_date: datetime
  response:
    investigations: Investigation[]
    total: number
    page: number

GET /api/history/{id}:
  description: Get specific investigation details
  response:
    investigation: Investigation
    messages: ChatMessage[]
    tool_calls: ToolCall[]

DELETE /api/history/{id}:
  description: Delete investigation record
  response:
    success: boolean

GET /api/history/export:
  description: Export investigations as JSON
  query_params:
    from_date: datetime
    to_date: datetime
    ids: string[] (optional, specific IDs)
  response:
    Content-Type: application/json
    Content-Disposition: attachment
```

### 4.2 Health Check Endpoints

```yaml
# Backend (port 13001)
GET /health:
  response:
    status: healthy | degraded | unhealthy
    services:
      database: connected | disconnected
      mcp_server: connected | disconnected
      bedrock: connected | disconnected
    timestamp: datetime

# MCP Server (port 13002)
GET /health:
  response:
    status: healthy | unhealthy
    zabbix_instances:
      - id: string
        status: connected | disconnected
    timestamp: datetime

# Frontend (port 13000)
GET /health:
  response:
    status: ok
```

---

## 5. Configuration

### 5.1 Application Configuration

```yaml
# config/app.yaml
server:
  host: "0.0.0.0"
  port: 13001

polling:
  interval_seconds: 30

database:
  url: "${DATABASE_URL}"  # postgresql://user:pass@host:13432/db

mcp_server:
  url: "http://localhost:13002"

bedrock:
  region: "us-east-1"
  model_id: "anthropic.claude-3-sonnet-20240229-v1:0"

history:
  retention_days: 90

runbooks:
  path: "./runbooks"

logging:
  level: "INFO"
  format: "json"  # CloudWatch compatible
```

### 5.2 Instances Configuration

```yaml
# config/instances.yaml
instances:
  - id: "zabbix-local"
    name: "Local Zabbix 7.x"
    url: "http://localhost:13080/api_jsonrpc.php"
    username: "Admin"
    password: "${ZABBIX_LOCAL_PASSWORD}"
    timeout: 30
    enabled: true
    
  - id: "zabbix-dc1"
    name: "Production DC1"
    url: "https://zabbix-dc1.example.com/api_jsonrpc.php"
    username: "api_user"
    password: "${ZABBIX_DC1_PASSWORD}"
    timeout: 30
    enabled: true
    
  - id: "zabbix-dc2"
    name: "Production DC2"
    url: "https://zabbix-dc2.example.com/api_jsonrpc.php"
    username: "api_user"
    password: "${ZABBIX_DC2_PASSWORD}"
    timeout: 30
    enabled: true
```

### 5.3 Environment Variables

```bash
# .env file (local development)

# Database
DATABASE_URL=postgresql://noc_user:noc_password@localhost:13432/noc_db
POSTGRES_USER=noc_user
POSTGRES_PASSWORD=noc_password
POSTGRES_DB=noc_db

# Zabbix credentials
ZABBIX_LOCAL_PASSWORD=zabbix
ZABBIX_DC1_PASSWORD=secret123
ZABBIX_DC2_PASSWORD=secret456

# AWS (for Bedrock)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Service URLs (for inter-container communication)
MCP_SERVER_URL=http://localhost:13002
BACKEND_URL=http://localhost:13001
```


---

## 6. Docker Deployment

### 6.1 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    network_mode: host
    environment:
      - BACKEND_URL=http://localhost:13001
      - PORT=13000
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    network_mode: host
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:13432/${POSTGRES_DB}
      - MCP_SERVER_URL=http://localhost:13002
      - PORT=13001
      - AWS_REGION=${AWS_REGION}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    volumes:
      - ./config:/app/config:ro
      - ./runbooks:/app/runbooks:ro
    depends_on:
      postgres:
        condition: service_healthy
      mcp-server:
        condition: service_healthy
    restart: unless-stopped

  mcp-server:
    build:
      context: ./mcp-server
      dockerfile: Dockerfile
    network_mode: host
    environment:
      - PORT=13002
      - ZABBIX_DC1_PASSWORD=${ZABBIX_DC1_PASSWORD}
      - ZABBIX_DC2_PASSWORD=${ZABBIX_DC2_PASSWORD}
    volumes:
      - ./config:/app/config:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:13002/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    network_mode: host
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
      - PGPORT=13432
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} -p 13432"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  pgadmin:
    image: dpage/pgadmin4:latest
    network_mode: host
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@local.dev
      - PGADMIN_DEFAULT_PASSWORD=admin
      - PGADMIN_LISTEN_PORT=13050
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    depends_on:
      - postgres
    restart: unless-stopped

volumes:
  postgres_data:
  pgadmin_data:
```

### 6.2 Dockerfiles

**Frontend Dockerfile:**
```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/server.js ./
COPY --from=builder /app/package*.json ./
RUN npm ci --only=production
EXPOSE 13000
CMD ["node", "server.js"]
```

**Backend Dockerfile:**
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/

EXPOSE 13001
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "13001"]
```

**MCP Server Dockerfile:**
```dockerfile
# mcp-server/Dockerfile
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 13002
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:13002", "src.main:app"]
```

---

## 7. Instance Down Alarm Generation

### 7.1 Backend Instance Monitor

The backend monitors Zabbix instance connectivity and generates synthetic alarms when instances are unreachable.

```python
# src/services/instance_monitor.py
import asyncio
from datetime import datetime
from typing import Optional

class InstanceMonitor:
    def __init__(self, mcp_client, alarm_store):
        self.mcp_client = mcp_client
        self.alarm_store = alarm_store
        self.instance_status: dict[str, dict] = {}
        self.check_interval = 30  # seconds
    
    async def start(self):
        """Start monitoring loop."""
        while True:
            await self.check_all_instances()
            await asyncio.sleep(self.check_interval)
    
    async def check_all_instances(self):
        """Check all instances and generate alarms for down ones."""
        instances = await self.mcp_client.get_instances()
        
        for instance in instances:
            status = await self.mcp_client.check_instance_status(instance['id'])
            previous = self.instance_status.get(instance['id'], {})
            
            if status['status'] == 'error':
                # Instance is down
                if previous.get('status') != 'error':
                    # Transition to down - generate alarm
                    await self._generate_instance_down_alarm(instance, status)
                    
            elif status['status'] == 'connected':
                # Instance is up
                if previous.get('status') == 'error':
                    # Transition to up - clear alarm
                    await self._clear_instance_down_alarm(instance)
            
            self.instance_status[instance['id']] = status
    
    async def _generate_instance_down_alarm(self, instance: dict, status: dict):
        """Generate synthetic alarm for down instance."""
        alarm = {
            "id": f"synthetic-{instance['id']}-down",
            "instance_id": instance['id'],
            "instance_name": instance['name'],
            "host": f"Zabbix Server ({instance['name']})",
            "description": f"Zabbix instance '{instance['name']}' is unreachable: {status.get('error', 'Connection failed')}",
            "severity": "disaster",
            "severity_code": 5,
            "duration": "0s",
            "acknowledged": False,
            "event_id": f"synthetic-{instance['id']}-{datetime.utcnow().timestamp()}",
            "is_synthetic": True,
            "started_at": datetime.utcnow().isoformat()
        }
        self.alarm_store.add_synthetic_alarm(alarm)
    
    async def _clear_instance_down_alarm(self, instance: dict):
        """Remove synthetic alarm when instance recovers."""
        self.alarm_store.remove_synthetic_alarm(f"synthetic-{instance['id']}-down")
```

### 7.2 Alarm Store with Synthetic Alarms

```python
# src/services/alarm_aggregator.py
from datetime import datetime

class AlarmAggregator:
    def __init__(self):
        self.zabbix_alarms: list[dict] = []
        self.synthetic_alarms: dict[str, dict] = {}
        self.last_poll: datetime = None
    
    def set_zabbix_alarms(self, alarms: list[dict]):
        """Update alarms from Zabbix polling."""
        self.zabbix_alarms = alarms
        self.last_poll = datetime.utcnow()
    
    def add_synthetic_alarm(self, alarm: dict):
        """Add synthetic alarm (e.g., instance down)."""
        self.synthetic_alarms[alarm['id']] = alarm
    
    def remove_synthetic_alarm(self, alarm_id: str):
        """Remove synthetic alarm."""
        self.synthetic_alarms.pop(alarm_id, None)
    
    def get_all_alarms(self) -> list[dict]:
        """Get combined list of Zabbix + synthetic alarms."""
        all_alarms = list(self.synthetic_alarms.values()) + self.zabbix_alarms
        # Sort by severity (desc) then time (desc)
        return sorted(all_alarms, key=lambda a: (-a['severity_code'], a.get('started_at', '')), reverse=False)
```

### 7.3 Frontend Instance Down Display

```typescript
// Synthetic alarms are displayed with special styling
interface Alarm {
  id: string;
  instance_id: string;
  instance_name: string;
  host: string;
  description: string;
  severity: string;
  severity_code: number;
  duration: string;
  acknowledged: boolean;
  is_synthetic?: boolean;  // True for instance-down alarms
}

// In AlarmTable.tsx
const AlarmRow = ({ alarm }: { alarm: Alarm }) => (
  <TableRow 
    sx={{ 
      backgroundColor: alarm.is_synthetic ? 'rgba(244, 67, 54, 0.1)' : 'inherit',
      borderLeft: alarm.is_synthetic ? '4px solid #f44336' : 'none'
    }}
  >
    {/* ... row content ... */}
    {alarm.is_synthetic && (
      <Chip label="SYSTEM" size="small" color="error" />
    )}
  </TableRow>
);
```

---

## 8. AWS Migration Path

### 8.1 EKS Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                        VPC                                 │  │
│  │  ┌─────────────────┐  ┌─────────────────────────────────┐ │  │
│  │  │   Public Subnet │  │        Private Subnet           │ │  │
│  │  │  ┌───────────┐  │  │  ┌─────────────────────────┐   │ │  │
│  │  │  │    ALB    │  │  │  │      EKS Cluster        │   │ │  │
│  │  │  └─────┬─────┘  │  │  │  ┌─────┐ ┌─────┐ ┌────┐│   │ │  │
│  │  │        │        │  │  │  │Front│ │Back │ │MCP ││   │ │  │
│  │  │        │        │  │  │  │end  │ │end  │ │Srv ││   │ │  │
│  │  │        │        │  │  │  └─────┘ └─────┘ └────┘│   │ │  │
│  │  └────────┼────────┘  │  └────────────┬────────────┘   │ │  │
│  │           │           │               │                 │ │  │
│  │           └───────────┼───────────────┘                 │ │  │
│  │                       │                                 │ │  │
│  │  ┌────────────────────┼─────────────────────────────┐  │ │  │
│  │  │                    │    Data Subnet              │  │ │  │
│  │  │  ┌─────────────────▼───┐  ┌───────────────────┐  │  │ │  │
│  │  │  │    RDS PostgreSQL   │  │  Secrets Manager  │  │  │ │  │
│  │  │  └─────────────────────┘  └───────────────────┘  │  │ │  │
│  │  └──────────────────────────────────────────────────┘  │ │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │  Amazon Bedrock   │                        │
│                    └───────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Kubernetes Manifests (Future)

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: noc-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: noc-backend
  template:
    spec:
      containers:
      - name: backend
        image: ${ECR_REPO}/noc-backend:latest
        ports:
        - containerPort: 13001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: noc-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /health
            port: 13001
        readinessProbe:
          httpGet:
            path: /health
            port: 13001
```

---

## 9. Project Structure Summary

```
noc-troubleshoot-assistant/
├── docker-compose.yml
├── .env.example
├── README.md
├── config/
│   ├── app.yaml
│   └── instances.yaml
├── runbooks/
│   ├── by-trigger/
│   │   ├── high-cpu-usage.md
│   │   └── disk-space-low.md
│   ├── by-service/
│   │   ├── mysql/
│   │   └── nginx/
│   └── general/
│       └── escalation.md
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── server.js
│   └── src/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── init.sql
│   └── src/
├── mcp-server/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
├── k8s/                    # Future AWS/EKS
│   ├── namespace.yaml
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   └── mcp-server-deployment.yaml
└── doc/
    ├── detailed_requirements.md
    ├── functional_specification.md
    └── design_specification.md
```

---

## 10. Dependencies

### 10.1 Backend (requirements.txt)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
pydantic==2.5.3
pydantic-settings==2.1.0
httpx==0.26.0
strands-agents==0.1.0
boto3==1.34.0
pyyaml==6.0.1
python-multipart==0.0.6
```

### 10.2 MCP Server (requirements.txt)
```
flask==3.0.0
gunicorn==21.2.0
zabbix-utils==2.0.0
pyyaml==6.0.1
```

### 10.3 Frontend (package.json dependencies)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@mui/material": "^5.15.0",
    "@mui/icons-material": "^5.15.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "zustand": "^4.4.0",
    "react-markdown": "^9.0.0",
    "date-fns": "^3.0.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@types/react": "^18.2.0"
  }
}
```

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12-15 | Initial design specification |
