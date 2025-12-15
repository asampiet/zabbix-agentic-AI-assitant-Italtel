# Network Troubleshooting Chat Assistant - Detailed Requirements

## 1. Project Overview

### 1.1 Purpose
Build an AI-powered chat assistant for network engineers to troubleshoot network problems using Zabbix monitoring data. The system provides an agentic interface that interacts with multiple Zabbix instances through MCP (Model Context Protocol) servers.

### 1.2 Key Features
- Multi-instance Zabbix monitoring dashboard
- Real-time alarm visualization with configurable polling
- AI-powered investigation assistant
- Structured runbooks for issue resolution
- Full audit trail with export capability

---

## 2. Technical Stack

### 2.1 Frontend
- **Framework**: React + TypeScript
- **UI Library**: Material-UI (MUI) - matching existing NOC Operations Center layout
- **State Management**: Redux Toolkit
- **Styling**: MUI theme system (dark theme, consistent with existing NOC app)

### 2.2 Backend
- **Runtime**: Python 3.11+
- **Framework**: FastAPI
- **MCP Server**: FastMCP (python-zabbix-utils integration)
- **LLM Provider**: Amazon Bedrock (Claude)

### 2.3 Infrastructure
- **Deployment**: Docker containers (docker-compose)
- **Data Storage**: Local filesystem (runbooks as markdown files)

---

## 3. Architecture

### 3.1 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Interface                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Instance     │  │ Alarm        │  │ Chat Interface       │  │
│  │ Dashboard    │  │ Panel        │  │ (Investigation)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend API (FastAPI)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Alarm        │  │ Investigation│  │ History              │  │
│  │ Aggregator   │  │ Service      │  │ Service              │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Server (Zabbix)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Single MCP Server with instance selection per tool call   │  │
│  │ - host_get, host_create, host_update, host_delete        │  │
│  │ - problem_get, event_get, event_acknowledge              │  │
│  │ - trigger_get, trigger_create, trigger_update            │  │
│  │ - template_get, item_get, history_get                    │  │
│  │ - maintenance_get, maintenance_create                    │  │
│  │ - configuration_export, configuration_import             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Zabbix Instances (7.x)                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │ Instance 1 │  │ Instance 2 │  │ Instance N │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 MCP Server Structure
Based on the existing `mcp_zabbix.txt` documentation, the MCP server will be a **single server with instance selection per tool call**. Each tool accepts an `instance_id` parameter to target the appropriate Zabbix instance.

**Available MCP Tools:**
| Category | Tools |
|----------|-------|
| Host Management | `host_get`, `host_create`, `host_update`, `host_delete` |
| Host Groups | `hostgroup_get`, `hostgroup_create`, `hostgroup_update`, `hostgroup_delete` |
| Items | `item_get`, `item_create`, `item_update`, `item_delete` |
| Triggers | `trigger_get`, `trigger_create`, `trigger_update`, `trigger_delete` |
| Templates | `template_get`, `template_create`, `template_update`, `template_delete` |
| Problems/Events | `problem_get`, `event_get`, `event_acknowledge` |
| Data | `history_get`, `trend_get` |
| Users | `user_get`, `user_create`, `user_update`, `user_delete` |
| Proxies | `proxy_get`, `proxy_create`, `proxy_update`, `proxy_delete` |
| Maintenance | `maintenance_get`, `maintenance_create`, `maintenance_update`, `maintenance_delete` |
| Graphs | `graph_get` |
| Discovery | `discoveryrule_get`, `itemprototype_get` |
| Configuration | `configuration_export`, `configuration_import` |
| System | `apiinfo_version` |

---

## 4. Functional Requirements

### 4.1 Zabbix Instance Management

#### 4.1.1 Instance Configuration
- **FR-4.1.1**: Store all Zabbix instance configurations in a single YAML/JSON configuration file
- **FR-4.1.2**: Each instance configuration includes:
  - Instance ID (unique identifier)
  - Display name
  - API URL
  - Authentication credentials (username/password)
  - Connection timeout settings
  - Enabled/disabled status

#### 4.1.2 Instance Display
- **FR-4.1.3**: Display all configured instances as cards on the dashboard
- **FR-4.1.4**: Each instance card shows:
  - Instance name
  - Connection status (connected/disconnected/error)
  - Active problem count by severity
  - Last sync timestamp
- **FR-4.1.5**: Visual indicators for instance health (green/yellow/red)

### 4.2 Alarm Management

#### 4.2.1 Alarm Retrieval
- **FR-4.2.1**: Poll all Zabbix instances for active problems at configurable intervals (default: 30 seconds)
- **FR-4.2.2**: Support all severity levels:
  - Not classified (0)
  - Information (1)
  - Warning (2)
  - Average (3)
  - High (4)
  - Disaster (5)
- **FR-4.2.3**: Aggregate alarms from all instances into a unified view

#### 4.2.2 Alarm Display
- **FR-4.2.4**: Display alarms in a sortable, filterable table
- **FR-4.2.5**: Table columns:
  - Severity (with color coding)
  - Instance name
  - Host name
  - Problem description
  - Duration
  - Acknowledged status
  - Investigation button
- **FR-4.2.6**: Filter alarms by:
  - Instance
  - Severity
  - Host
  - Acknowledged status
  - Time range

#### 4.2.3 Alarm Actions
- **FR-4.2.7**: "Investigate" button triggers AI-powered investigation
- **FR-4.2.8**: Acknowledge alarms directly from the UI
- **FR-4.2.9**: View alarm history and related events

### 4.3 Chat Interface

#### 4.3.1 User Interaction
- **FR-4.3.1**: Text input for user queries
- **FR-4.3.2**: Message history display with user/assistant distinction
- **FR-4.3.3**: Support for markdown rendering in responses
- **FR-4.3.4**: Code block syntax highlighting
- **FR-4.3.5**: Loading indicators during AI processing

#### 4.3.2 Investigation Flow
- **FR-4.3.6**: When "Investigate" is clicked:
  1. Pre-populate chat with alarm context
  2. Agent automatically calls relevant MCP tools
  3. Agent analyzes collected data
  4. Agent provides diagnosis and runbook
- **FR-4.3.7**: Agent can request additional information from user
- **FR-4.3.8**: Agent can execute follow-up queries to Zabbix

#### 4.3.3 Agent Capabilities
- **FR-4.3.9**: Full Zabbix management through MCP tools:
  - Read operations (hosts, triggers, problems, history)
  - Acknowledge alarms
  - Execute remediation (create/modify hosts, triggers)
  - Full configuration management
- **FR-4.3.10**: Context-aware responses based on alarm data
- **FR-4.3.11**: Runbook retrieval and presentation

### 4.4 Runbook System

#### 4.4.1 Runbook Storage
- **FR-4.4.1**: Store runbooks as local markdown files in repository
- **FR-4.4.2**: Runbook directory structure:
  ```
  runbooks/
  ├── by-trigger/
  │   ├── high-cpu-usage.md
  │   ├── disk-space-low.md
  │   └── ...
  ├── by-service/
  │   ├── mysql/
  │   ├── nginx/
  │   └── ...
  └── general/
      ├── escalation-procedures.md
      └── ...
  ```

#### 4.4.2 Runbook Format
- **FR-4.4.3**: Each runbook contains:
  - **Title**: Problem name
  - **Description**: Detailed problem explanation
  - **Root Causes**: Common causes list
  - **Diagnostic Steps**: Metrics and logs to check
  - **Resolution Steps**: Step-by-step fix instructions
  - **Automated Scripts**: Suggested remediation commands
  - **Escalation Path**: When and who to escalate to

#### 4.4.3 Runbook Matching
- **FR-4.4.4**: Agent matches alarms to runbooks by:
  - Trigger name/description
  - Host group
  - Service type
- **FR-4.4.5**: Present matched runbook in chat response

### 4.5 Investigation History

#### 4.5.1 History Storage
- **FR-4.5.1**: Persist all investigation sessions
- **FR-4.5.2**: Store per investigation:
  - Timestamp (start/end)
  - Alarm details
  - Chat transcript
  - MCP tool calls and responses
  - Resolution status
  - User notes

#### 4.5.2 History Retention
- **FR-4.5.3**: Configurable retention period (default: 90 days)
- **FR-4.5.4**: Automatic cleanup of expired records
- **FR-4.5.5**: Manual deletion capability

#### 4.5.3 History Export
- **FR-4.5.6**: Export investigation history in multiple formats:
  - JSON (full data)
  - CSV (summary)
  - PDF (formatted report)
- **FR-4.5.7**: Bulk export with date range filter
- **FR-4.5.8**: Include all audit trail data in exports

---

## 5. Non-Functional Requirements

### 5.1 Performance
- **NFR-5.1.1**: Frontend initial load < 3 seconds
- **NFR-5.1.2**: Alarm polling cycle < 5 seconds per instance
- **NFR-5.1.3**: Chat response initiation < 2 seconds
- **NFR-5.1.4**: Support up to 10 Zabbix instances simultaneously

### 5.2 Reliability
- **NFR-5.2.1**: Graceful handling of Zabbix instance unavailability
- **NFR-5.2.2**: Automatic reconnection on connection loss
- **NFR-5.2.3**: No data loss on browser refresh

### 5.3 Security
- **NFR-5.3.1**: Zabbix credentials stored securely (environment variables or secrets file)
- **NFR-5.3.2**: No credentials exposed in frontend
- **NFR-5.3.3**: HTTPS support for production deployment

### 5.4 Usability
- **NFR-5.4.1**: Responsive design (desktop-first, tablet-compatible)
- **NFR-5.4.2**: Dark theme (matching existing NOC Operations Center)
- **NFR-5.4.3**: Keyboard shortcuts for common actions
- **NFR-5.4.4**: English language interface

---

## 6. UI/UX Specifications

### 6.1 Layout (Matching NOC Operations Center)
```
┌─────────────────────────────────────────────────────────────────┐
│                         Header Bar                               │
│  [Logo] Network Troubleshooting Assistant    [Settings] [User]  │
├─────────────────────────────────────────────────────────────────┤
│                    Connection Status Bar                         │
│  [Instance 1: ●] [Instance 2: ●] [Instance 3: ○] [Bedrock: ●]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐ │
│  │     Instance Cards          │  │    Chat Interface        │ │
│  │  ┌─────┐ ┌─────┐ ┌─────┐   │  │                          │ │
│  │  │ Z1  │ │ Z2  │ │ Z3  │   │  │  [Message History]       │ │
│  │  └─────┘ └─────┘ └─────┘   │  │                          │ │
│  │                             │  │                          │ │
│  │     Alarm Table             │  │                          │ │
│  │  ┌─────────────────────┐   │  │                          │ │
│  │  │ Sev │ Host │ Problem│   │  │                          │ │
│  │  │ 🔴  │ srv1 │ CPU... │   │  │  [Input Box]             │ │
│  │  │ 🟡  │ srv2 │ Disk...│   │  │                          │ │
│  │  └─────────────────────┘   │  └──────────────────────────┘ │
│  └─────────────────────────────┘                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Color Scheme
| Element | Color |
|---------|-------|
| Background | `#121212` (dark) |
| Surface | `#1e1e1e` |
| Primary | `#90caf9` (blue) |
| Severity - Disaster | `#f44336` (red) |
| Severity - High | `#ff9800` (orange) |
| Severity - Average | `#ffeb3b` (yellow) |
| Severity - Warning | `#8bc34a` (light green) |
| Severity - Information | `#2196f3` (blue) |
| Severity - Not classified | `#9e9e9e` (gray) |

### 6.3 Components
- **Header**: App title, settings, user menu
- **Connection Status Bar**: Real-time status of all connections
- **Instance Cards**: Grid of Zabbix instance status cards
- **Alarm Table**: Sortable, filterable alarm list
- **Chat Interface**: Message list + input (right panel)
- **Investigation Modal**: Detailed view during investigation

---

## 7. API Specifications

### 7.1 Backend REST API

#### Instances
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/instances` | List all configured instances |
| GET | `/api/instances/{id}/status` | Get instance connection status |

#### Alarms
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/alarms` | Get aggregated alarms from all instances |
| GET | `/api/alarms/{instance_id}` | Get alarms for specific instance |
| POST | `/api/alarms/{id}/acknowledge` | Acknowledge an alarm |

#### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message to AI agent |
| POST | `/api/chat/investigate` | Start investigation for alarm |
| GET | `/api/chat/history/{session_id}` | Get chat history |

#### History
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/history` | List investigation history |
| GET | `/api/history/{id}` | Get specific investigation |
| DELETE | `/api/history/{id}` | Delete investigation record |
| GET | `/api/history/export` | Export history (JSON/CSV/PDF) |

#### Runbooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/runbooks` | List available runbooks |
| GET | `/api/runbooks/{id}` | Get specific runbook content |

### 7.2 WebSocket (Future Enhancement)
- Currently using polling; WebSocket can be added for real-time updates

---

## 8. Configuration

### 8.1 Instance Configuration File
```yaml
# config/instances.yaml
instances:
  - id: "zabbix-prod-1"
    name: "Production DC1"
    url: "https://zabbix-dc1.example.com/api_jsonrpc.php"
    username: "api_user"
    password: "${ZABBIX_DC1_PASSWORD}"  # Environment variable reference
    timeout: 30
    enabled: true
    
  - id: "zabbix-prod-2"
    name: "Production DC2"
    url: "https://zabbix-dc2.example.com/api_jsonrpc.php"
    username: "api_user"
    password: "${ZABBIX_DC2_PASSWORD}"
    timeout: 30
    enabled: true
```

### 8.2 Application Configuration
```yaml
# config/app.yaml
polling:
  interval_seconds: 30  # Configurable polling interval
  
history:
  retention_days: 90  # Configurable retention period
  
bedrock:
  region: "us-east-1"
  model_id: "anthropic.claude-3-sonnet-20240229-v1:0"
  
runbooks:
  path: "./runbooks"
```

---

## 9. Deployment

### 9.1 Docker Compose Structure
```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
      
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - AWS_REGION=us-east-1
      - ZABBIX_DC1_PASSWORD=${ZABBIX_DC1_PASSWORD}
    volumes:
      - ./config:/app/config
      - ./runbooks:/app/runbooks
      - ./data:/app/data
      
  mcp-server:
    build: ./mcp-server
    ports:
      - "8001:8001"
    environment:
      - ZABBIX_DC1_PASSWORD=${ZABBIX_DC1_PASSWORD}
    volumes:
      - ./config:/app/config
```

### 9.2 Directory Structure
```
project/
├── docker-compose.yml
├── config/
│   ├── instances.yaml
│   └── app.yaml
├── runbooks/
│   ├── by-trigger/
│   ├── by-service/
│   └── general/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
├── mcp-server/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
└── data/
    └── history/
```

---

## 10. Future Enhancements (Out of Scope)

The following features are identified for future releases:
- WebSocket real-time updates
- Multi-language support (i18n)
- External notifications (email, Slack, Teams)
- Role-based access control
- SSO/LDAP integration
- Vector database for semantic runbook search
- Automated remediation execution

---

## 11. Acceptance Criteria

### 11.1 MVP Acceptance
- [ ] Display multiple Zabbix instances with connection status
- [ ] Show aggregated alarms from all instances
- [ ] Polling updates alarms every 30 seconds (configurable)
- [ ] "Investigate" button triggers AI analysis
- [ ] Chat interface displays conversation history
- [ ] Agent retrieves data via MCP tools
- [ ] Agent provides runbook-based recommendations
- [ ] Investigation history is persisted and exportable
- [ ] Docker deployment works with docker-compose up

### 11.2 Quality Gates
- [ ] All API endpoints return proper error responses
- [ ] Frontend handles connection failures gracefully
- [ ] No credentials exposed in browser
- [ ] UI matches existing NOC Operations Center styling

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-15 | Network Engineering Team | Initial requirements |
