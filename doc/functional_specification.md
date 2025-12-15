# Network Troubleshooting Chat Assistant - Functional Specification

## Document Information
| Field | Value |
|-------|-------|
| Version | 1.0 |
| Date | 2024-12-15 |
| Status | Draft |
| Related | detailed_requirements.md |

---

## 1. Overview

This document defines the functional behavior of the Network Troubleshooting Chat Assistant, detailing user interactions, system responses, and business logic.

---

## 2. User Roles

### 2.1 Network Engineer (Single Role)
- No authentication required (single-user access)
- Full access to all features
- Can view, investigate, and acknowledge alarms
- Can interact with AI agent for troubleshooting

---

## 3. Functional Modules

### 3.1 Dashboard Module

#### 3.1.1 Instance Cards

**Display:**
- Grid layout showing all configured Zabbix instances
- Each card displays:
  - Instance name
  - Connection status indicator (green/red)
  - Problem count badges by severity
  - Last sync timestamp

**Interactions:**

| Action | Behavior |
|--------|----------|
| Single click | Filter alarm table to show only that instance's alarms |
| Double click | Open modal with detailed instance information |

**Instance Detail Modal Contents:**
- Instance name and URL
- Connection status and uptime
- API version
- Total hosts count
- Active problems breakdown by severity
- "Close" button

---

#### 3.1.2 Connection Status Bar

**Display:**
- Horizontal bar below header
- Shows connection status for each Zabbix instance
- Shows Amazon Bedrock connection status
- Color-coded indicators: ● Green (connected), ○ Gray (disconnected), ● Red (error)

**Polling Status:**
- Displays "Last updated: [timestamp]"
- "Refresh Now" button for manual refresh
- Clicking "Refresh Now" triggers immediate poll of all instances

---

### 3.2 Alarm Management Module

#### 3.2.1 Alarm Table

**Default View:**
- Shows all alarms from all instances
- Sorted by severity (Disaster → High → Average → Warning → Information → Not classified)
- Secondary sort by time (newest first within same severity)

**Table Columns:**

| Column | Description | Sortable | Filterable |
|--------|-------------|----------|------------|
| Severity | Color-coded badge | Yes | Yes (multi-select) |
| Instance | Zabbix instance name | Yes | Yes (multi-select) |
| Host | Host name (clickable) | Yes | Yes (text search) |
| Problem | Trigger description | Yes | Yes (text search) |
| Duration | Time since problem started | Yes | Yes (range) |
| Ack | Acknowledged status icon | Yes | Yes (yes/no) |
| Actions | Investigate, Acknowledge buttons | No | No |

**Filter Behavior:**
- Filters persist in browser localStorage
- Reset on page reload (no server persistence)
- "Clear Filters" button resets all filters

**Polling Behavior:**
- Table refreshes silently every 30 seconds (configurable)
- No notification on new alarms
- Maintains current scroll position and selection on refresh

---

#### 3.2.2 Host Drill-Down

**Trigger:** Click on host name in alarm table

**Behaviors:**
- Single click on host name: Filter alarm table to show all alarms for that host
- Click host name + hold Shift: Open host detail modal

**Host Detail Modal Contents:**
- Host name and IP addresses
- Host groups
- Active problems list
- Recent items/metrics (last 1 hour)
- Associated triggers
- Link to Zabbix web interface
- "Close" button

---

#### 3.2.3 Alarm Acknowledgment

**Trigger:** Click "Acknowledge" button (checkmark icon) in alarm row

**Behavior:**
- One-click acknowledgment (no confirmation dialog)
- No additional message required
- Immediate API call to Zabbix
- Row updates to show acknowledged status
- Toast notification: "Alarm acknowledged"

**Error Handling:**
- On failure: Toast error "Failed to acknowledge alarm. Please retry."
- Row remains in unacknowledged state

---

### 3.3 Chat Interface Module

#### 3.3.1 Chat Layout

**Position:** Right panel (flex: 1, min-width: 400px)

**Components:**
- Message history area (scrollable)
- Input text box (bottom)
- Send button

**Session Management:**
- One global chat session
- All investigations share the same conversation
- History persists until browser refresh or explicit clear

---

#### 3.3.2 Investigation Flow

**Trigger:** Click "Investigate" button in alarm row

**Automatic Behavior:**
1. Chat panel receives focus
2. System message appears: "Starting investigation for: [Problem Description]"
3. Context automatically loaded:
   - Alarm ID and description
   - Host details (name, IP, groups)
   - Recent metrics (last 1 hour of relevant items)
4. Agent immediately begins analysis (no user confirmation needed)
5. Agent displays: "Analyzing [host]..." with tool indicators

**Agent Tool Visibility:**
- Show tool names during execution
- Format: "🔍 Querying host data..." / "📊 Retrieving metrics..." / "🔧 Checking triggers..."
- Hide parameters and raw responses
- Show only final synthesized response

---

#### 3.3.3 Message Types

**User Message:**
```
┌─────────────────────────────────┐
│ [User Avatar]                   │
│ User message text here          │
│                      [timestamp]│
└─────────────────────────────────┘
```

**Assistant Message:**
```
┌─────────────────────────────────┐
│ [Bot Avatar]                    │
│ Assistant response with         │
│ **markdown** support            │
│ - Bullet points                 │
│ - Code blocks                   │
│                      [timestamp]│
└─────────────────────────────────┘
```

**System Message:**
```
┌─────────────────────────────────┐
│ ℹ️ System notification          │
│ (centered, muted color)         │
└─────────────────────────────────┘
```

**Tool Indicator:**
```
┌─────────────────────────────────┐
│ 🔍 Querying host data...        │
│ (animated spinner)              │
└─────────────────────────────────┘
```

---

#### 3.3.4 Runbook Presentation

**Display Method:** Agent summarizes key steps inline, with "View Full Runbook" button

**Inline Summary Format:**
```
Based on the alarm, here's the recommended action:

**Problem:** High CPU Usage on srv-web-01
**Likely Cause:** Process consuming excessive resources

**Quick Steps:**
1. Check top processes: `top -o %CPU`
2. Identify runaway process
3. Consider restarting service if safe

[View Full Runbook] [Open in Side Panel]
```

**"View Full Runbook" Button:**
- Opens side panel (slides in from right)
- Shows complete runbook markdown content
- Panel can be closed without losing chat context

**Side Panel Contents:**
- Runbook title
- Full markdown content (scrollable)
- "Copy to Clipboard" button
- "Close" button

---

#### 3.3.5 Error Handling

**Scenario:** Agent fails to retrieve data (timeout, connection error)

**Behavior:**
1. Display error message in chat:
   ```
   ⚠️ Unable to retrieve data from [Instance Name]: Connection timeout
   
   [Retry] [Skip and Continue]
   
   Suggested actions:
   • Check if Zabbix instance is accessible
   • Verify network connectivity
   • Try investigating a different alarm
   ```

2. "Retry" button: Re-attempts the failed operation
3. "Skip and Continue": Agent continues with available data, notes limitation

---

### 3.4 Investigation History Module

#### 3.4.1 History List View

**Access:** Menu item "History" or dedicated tab

**Display:**
- Table/list of past investigations
- Columns: Date, Alarm, Instance, Host, Duration, Status

**Search & Filter:**
- Full-text search across transcripts
- Filter by:
  - Date range (date picker)
  - Instance (multi-select)
  - Severity (multi-select)
- Saved search presets (stored in localStorage)

**Preset Management:**
- "Save Current Filter" button
- Preset name input
- List of saved presets in dropdown
- Delete preset option

---

#### 3.4.2 History Detail View

**Trigger:** Click on history row

**Display:**
- Investigation metadata (date, duration, alarm details)
- Full chat transcript (read-only)
- List of MCP tool calls made
- Resolution status

**Actions:**
- "Export" button → Downloads JSON file
- "Delete" button → Confirmation dialog → Remove record
- "Close" button

---

#### 3.4.3 History Export

**Single Investigation Export:**
- Format: JSON only
- Contains:
  - Investigation metadata
  - Alarm details
  - Full chat transcript
  - Tool calls and responses
  - Timestamps

**Bulk Export:**
- Access via "Export All" button with current filters applied
- Format: JSON (array of investigations)
- Date range selector for export scope

**JSON Export Schema:**
```json
{
  "export_date": "2024-12-15T10:30:00Z",
  "investigations": [
    {
      "id": "inv-001",
      "started_at": "2024-12-15T09:00:00Z",
      "ended_at": "2024-12-15T09:15:00Z",
      "alarm": {
        "id": "12345",
        "severity": "high",
        "description": "CPU usage above 90%",
        "host": "srv-web-01",
        "instance": "zabbix-prod-1"
      },
      "transcript": [
        {
          "role": "system",
          "content": "Starting investigation...",
          "timestamp": "2024-12-15T09:00:00Z"
        },
        {
          "role": "assistant",
          "content": "Analyzing host srv-web-01...",
          "timestamp": "2024-12-15T09:00:05Z"
        }
      ],
      "tool_calls": [
        {
          "tool": "host_get",
          "parameters": {"host": "srv-web-01"},
          "timestamp": "2024-12-15T09:00:02Z"
        }
      ],
      "resolution": "resolved"
    }
  ]
}
```

---

### 3.5 Concurrent Operations

#### 3.5.1 Investigation Concurrency

**Rule:** One investigation at a time

**Behavior when starting new investigation:**
- If no active investigation: Start immediately
- If investigation in progress:
  - Show confirmation: "An investigation is in progress. Start new investigation?"
  - "Continue Current" → Return to existing chat
  - "Start New" → Save current to history, start fresh

---

## 4. Navigation & Layout

### 4.1 Main Layout Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER                                                          │
│ [Logo] Network Troubleshooting Assistant         [History] [⚙️] │
├─────────────────────────────────────────────────────────────────┤
│ CONNECTION STATUS BAR                                           │
│ Zabbix-DC1: ● | Zabbix-DC2: ● | Bedrock: ●  Last: 10:30 [🔄]   │
├───────────────────────────────────┬─────────────────────────────┤
│ MAIN PANEL (flex: 2)              │ CHAT PANEL (flex: 1)        │
│                                   │                             │
│ ┌─────────────────────────────┐   │ ┌─────────────────────────┐ │
│ │ Instance Cards (horizontal) │   │ │                         │ │
│ │ [Card1] [Card2] [Card3]     │   │ │   Message History       │ │
│ └─────────────────────────────┘   │ │                         │ │
│                                   │ │                         │ │
│ ┌─────────────────────────────┐   │ │                         │ │
│ │ Alarm Table                 │   │ │                         │ │
│ │ [Filters]                   │   │ │                         │ │
│ │ ┌─────────────────────────┐ │   │ │                         │ │
│ │ │ Sev │ Host │ Problem   │ │   │ ├─────────────────────────┤ │
│ │ │ 🔴  │ srv1 │ CPU high  │ │   │ │ [Type message...]  [➤] │ │
│ │ │ 🟡  │ srv2 │ Disk low  │ │   │ └─────────────────────────┘ │
│ │ └─────────────────────────┘ │   │                             │
│ └─────────────────────────────┘   │                             │
└───────────────────────────────────┴─────────────────────────────┘
```

### 4.2 Header Actions

| Element | Action |
|---------|--------|
| Logo | Refresh page / Return to dashboard |
| History | Open investigation history view |
| Settings (⚙️) | Open settings modal (polling interval, theme) |

---

## 5. State Management

### 5.1 Application State

```typescript
interface AppState {
  // Instances
  instances: Instance[];
  instanceStatus: Record<string, ConnectionStatus>;
  selectedInstance: string | null;  // For filtering
  
  // Alarms
  alarms: Alarm[];
  alarmFilters: AlarmFilters;
  lastPollTime: Date;
  isPolling: boolean;
  
  // Chat
  messages: ChatMessage[];
  isAgentProcessing: boolean;
  currentInvestigation: Investigation | null;
  
  // History
  investigations: Investigation[];
  historyFilters: HistoryFilters;
  savedFilterPresets: FilterPreset[];
  
  // UI
  sidePanel: 'closed' | 'runbook' | 'host-detail' | 'instance-detail';
  sidePanelContent: any;
}
```

### 5.2 Persistence

| Data | Storage | Lifetime |
|------|---------|----------|
| Alarm filters | localStorage | Until page reload |
| Chat messages | Memory (Redux) | Until page reload |
| Investigation history | Backend API | Configurable retention |
| Filter presets | localStorage | Persistent |
| Settings | localStorage | Persistent |

---

## 6. API Interactions

### 6.1 Polling Sequence

```
Every 30 seconds:
1. GET /api/instances → Update instance status
2. GET /api/alarms → Update alarm table
3. Update lastPollTime
```

### 6.2 Investigation Sequence

```
User clicks "Investigate":
1. POST /api/chat/investigate
   Body: { alarm_id, instance_id }
   
2. Backend:
   a. Load alarm context
   b. Call MCP tools (host_get, item_get, history_get)
   c. Send to Bedrock with context
   d. Stream response back

3. Frontend:
   a. Display tool indicators
   b. Render streamed response
   c. Save to investigation history
```

### 6.3 Acknowledgment Sequence

```
User clicks "Acknowledge":
1. POST /api/alarms/{id}/acknowledge
   Body: { instance_id }
   
2. Backend:
   a. Call MCP event_acknowledge tool
   b. Return success/failure

3. Frontend:
   a. Update alarm row status
   b. Show toast notification
```

---

## 7. Error States

### 7.1 Connection Errors

| Scenario | UI Behavior |
|----------|-------------|
| Zabbix instance unreachable | Instance card shows red status, alarms from that instance marked as "stale" |
| Bedrock unavailable | Chat shows error, "Retry" button, investigation disabled |
| Network offline | Banner: "No network connection", polling paused |

### 7.2 Data Errors

| Scenario | UI Behavior |
|----------|-------------|
| Invalid alarm ID | Toast: "Alarm not found", remove from table |
| Empty response | Show "No data available" in relevant section |
| Timeout | Show error with "Retry" button |

---

## 8. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + Enter` | Send chat message |
| `Escape` | Close side panel / modal |
| `R` | Refresh alarms (when not in input field) |
| `F` | Focus filter input |

---

## 9. Acceptance Criteria

### 9.1 Dashboard
- [ ] Instance cards display with correct status colors
- [ ] Single click on card filters alarm table
- [ ] Double click opens instance detail modal
- [ ] Refresh button triggers immediate poll
- [ ] Last updated timestamp displays correctly

### 9.2 Alarm Table
- [ ] Default sort: severity (desc), then time (desc)
- [ ] All filter types work correctly
- [ ] Filters persist in localStorage
- [ ] Silent refresh maintains scroll position
- [ ] Host click filters table
- [ ] Host Shift+click opens modal

### 9.3 Chat Interface
- [ ] Investigate auto-starts agent analysis
- [ ] Tool indicators show during processing
- [ ] Runbook summary displays with "View Full" button
- [ ] Side panel opens with full runbook
- [ ] Error shows with Retry/Skip options

### 9.4 History
- [ ] Full-text search works across transcripts
- [ ] All filters work correctly
- [ ] Presets save and load correctly
- [ ] JSON export contains all required fields
- [ ] Delete removes record after confirmation

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12-15 | Initial functional specification |
