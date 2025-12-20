# Camunda Workflow Integration Guide - Time-Off Approval

## Overview

This document describes the integration between the ERP HR module and Camunda BPM for the Time-Off Approval workflow.

## Features

✅ **Camunda REST API Integration** - Full integration with Camunda workflow engine  
✅ **Message-Based Start Events** - Start workflows via messages  
✅ **Process Variable Management** - Pass data to/from workflows  
✅ **Task Completion** - Complete user tasks programmatically  
✅ **Workflow Monitoring** - Query workflow status and tasks  
✅ **Multi-Tenancy Support** - Tenant-aware workflow execution  
✅ **Graceful Degradation** - Continue operation if Camunda is unavailable  

## Architecture

```
┌──────────────────┐         HTTP REST API        ┌──────────────────┐
│                  │  ────────────────────────►   │                  │
│  ERP HR Service  │   Send Message/Complete Task │  Camunda BPM     │
│  (FastAPI)       │  ◄────────────────────────   │  Engine          │
│                  │   Query Status/Get Tasks     │                  │
└──────────────────┘                              └──────────────────┘
        │                                                  │
        │                                                  │
        ▼                                                  ▼
  ┌──────────┐                                      ┌──────────┐
  │ ERP DB   │                                      │ Camunda  │
  │ (Postgres│                                      │ DB       │
  └──────────┘                                      └──────────┘
```

## Camunda Client

### CamundaClient Class

Located in `app/clients/camunda_client.py`

**Key Methods:**

#### 1. send_message()
Send a message to start a workflow or trigger an intermediate event.

```python
response = await CamundaClient.send_message(
    message_name="TimeOffRequestMessage",
    business_key="timeoff-REQ-001",
    process_variables={
        "employeeId": "EMP-001",
        "startDate": "2024-02-01",
        "endDate": "2024-02-07",
        "reason": "Family vacation"
    },
    tenant_id="tenant-1"
)
```

#### 2. start_process()
Start a process instance directly.

```python
response = await CamundaClient.start_process(
    process_definition_key="TimeOffApproval",
    business_key="timeoff-REQ-001",
    variables={"employeeId": "EMP-001"},
    tenant_id="tenant-1"
)
```

#### 3. get_tasks()
Query pending tasks.

```python
tasks = await CamundaClient.get_tasks(
    process_instance_id="process-123",
    assignee="manager-456"
)
```

#### 4. complete_task()
Complete a user task.

```python
await CamundaClient.complete_task(
    task_id="task-789",
    variables={
        "approved": True,
        "approverComments": "Approved!"
    }
)
```

## Time-Off Approval Workflow

### BPMN Process Definition

**Process Key:** `TimeOffApproval`  
**Message Start Event:** `TimeOffRequestMessage`

### Workflow Steps

1. **Start Event** - Triggered by TimeOffRequestMessage
2. **Manager Approval** - User task assigned to employee's manager
3. **HR Review** (if > 5 days) - User task assigned to HR
4. **Update Status** - Service task to update request status
5. **Send Notification** - Service task to notify employee
6. **End Event** - Workflow complete

### Process Variables

```json
{
  "requestId": "REQ-001",
  "employeeId": "EMP-001",
  "employeeName": "John Doe",
  "employeeEmail": "john.doe@company.com",
  "timeOffType": "vacation",
  "startDate": "2024-02-01",
  "endDate": "2024-02-07",
  "daysRequested": 7,
  "reason": "Family vacation",
  "emergencyContact": "+1-555-0123",
  "submittedAt": "2024-01-15T10:00:00Z",
  "tenantId": "tenant-1",
  "status": "pending",
  "approved": null,
  "approverComments": null,
  "approvedBy": null,
  "approvedAt": null
}
```

## API Endpoints

### POST /api/hr/time-off/request

Submit a time-off request and start the Camunda workflow.

**Request:**
```json
{
  "employee_id": "EMP-001",
  "type": "vacation",
  "start_date": "2024-02-01",
  "end_date": "2024-02-07",
  "reason": "Family vacation to Hawaii",
  "emergency_contact": "+1-555-0123"
}
```

**Response (201):**
```json
{
  "success": true,
  "process_instance_id": "camunda-process-123",
  "business_key": "timeoff-REQ-001",
  "message": "Time-off request submitted successfully. Approval workflow started.",
  "time_off_request_id": "REQ-001"
}
```

**Flow:**
1. Validate request data
2. Generate unique request ID
3. Calculate days requested
4. Prepare process variables
5. Send message to Camunda
6. Save request to database
7. Return process instance ID

### GET /api/hr/time-off/requests

List time-off requests.

**Query Parameters:**
- `employee_id` - Filter by employee
- `status` - Filter by status (pending, approved, rejected)
- `skip` / `limit` - Pagination

**Response:**
```json
[
  {
    "id": "REQ-001",
    "employee_id": "EMP-001",
    "employee_name": "John Doe",
    "type": "vacation",
    "start_date": "2024-02-01",
    "end_date": "2024-02-07",
    "days_requested": 7,
    "status": "pending",
    "process_instance_id": "camunda-process-123",
    "current_task": "Manager Approval"
  }
]
```

### GET /api/hr/time-off/requests/{request_id}

Get details of a specific request including workflow status.

**Response:**
```json
{
  "id": "REQ-001",
  "employee_id": "EMP-001",
  "type": "vacation",
  "start_date": "2024-02-01",
  "end_date": "2024-02-07",
  "status": "pending",
  "process_instance_id": "camunda-process-123",
  "current_task": "Manager Approval"
}
```

### POST /api/hr/time-off/requests/{request_id}/approve

Approve or reject a time-off request (managers only).

**Request:**
```json
{
  "approved": true,
  "comments": "Approved. Enjoy your vacation!",
  "approved_by": "manager-123"
}
```

**Response:**
```json
{
  "success": true,
  "request_id": "REQ-001",
  "status": "approved",
  "message": "Time-off request approved successfully",
  "approved_by": "manager-123"
}
```

**Flow:**
1. Validate approver permission
2. Get pending Camunda tasks
3. Complete task with decision
4. Update request status in database
5. Send notification to employee

### DELETE /api/hr/time-off/requests/{request_id}

Cancel a pending time-off request.

**Flow:**
1. Verify request ownership
2. Cancel Camunda process instance
3. Update status to cancelled

### GET /api/hr/time-off/balance/{employee_id}

Get time-off balance for an employee.

**Response:**
```json
{
  "employee_id": "EMP-001",
  "balances": {
    "vacation": {
      "total_days": 20,
      "used_days": 5,
      "pending_days": 7,
      "available_days": 8
    },
    "sick_leave": {
      "total_days": 10,
      "used_days": 2,
      "available_days": 8
    }
  },
  "year": 2024
}
```

## Configuration

### Environment Variables

```bash
# Camunda BPM Workflow Engine
CAMUNDA_REST_URL=http://localhost:8080/engine-rest
CAMUNDA_ADMIN_USER=demo
CAMUNDA_ADMIN_PASSWORD=demo
CAMUNDA_TIMEOUT=30
```

### Application Config

```python
class Settings(BaseSettings):
    CAMUNDA_REST_URL: str = "http://localhost:8080/engine-rest"
    CAMUNDA_ADMIN_USER: str = "demo"
    CAMUNDA_ADMIN_PASSWORD: str = "demo"
    CAMUNDA_TIMEOUT: int = 30
```

## Camunda Setup

### 1. Install Camunda

```bash
# Download Camunda Platform Run
wget https://downloads.camunda.cloud/release/camunda-bpm/run/7.20/camunda-bpm-run-7.20.0.tar.gz

# Extract
tar -xzf camunda-bpm-run-7.20.0.tar.gz

# Start Camunda
cd camunda-bpm-run-7.20.0
./start.sh
```

### 2. Access Camunda

- **Cockpit:** http://localhost:8080/camunda/app/cockpit
- **Tasklist:** http://localhost:8080/camunda/app/tasklist
- **Admin:** http://localhost:8080/camunda/app/admin
- **REST API:** http://localhost:8080/engine-rest

**Default Credentials:**
- Username: `demo`
- Password: `demo`

### 3. Deploy BPMN Process

Create `TimeOffApproval.bpmn` and deploy via Cockpit or REST API:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:process id="TimeOffApproval" name="Time-Off Approval" isExecutable="true">
    
    <!-- Message Start Event -->
    <bpmn:startEvent id="StartEvent" name="Time-Off Request">
      <bpmn:messageEventDefinition messageRef="TimeOffRequestMessage"/>
    </bpmn:startEvent>
    
    <!-- Manager Approval Task -->
    <bpmn:userTask id="ManagerApproval" name="Manager Approval">
      <bpmn:incoming>Flow1</bpmn:incoming>
      <bpmn:outgoing>Flow2</bpmn:outgoing>
    </bpmn:userTask>
    
    <!-- Decision Gateway -->
    <bpmn:exclusiveGateway id="Gateway1">
      <bpmn:incoming>Flow2</bpmn:incoming>
      <bpmn:outgoing>FlowApproved</bpmn:outgoing>
      <bpmn:outgoing>FlowRejected</bpmn:outgoing>
    </bpmn:exclusiveGateway>
    
    <!-- Update Status Task -->
    <bpmn:serviceTask id="UpdateStatus" name="Update Status">
      <bpmn:incoming>FlowApproved</bpmn:incoming>
      <bpmn:incoming>FlowRejected</bpmn:incoming>
      <bpmn:outgoing>Flow3</bpmn:outgoing>
    </bpmn:serviceTask>
    
    <!-- End Event -->
    <bpmn:endEvent id="EndEvent" name="Request Processed">
      <bpmn:incoming>Flow3</bpmn:incoming>
    </bpmn:endEvent>
    
  </bpmn:process>
</bpmn:definitions>
```

## Testing

### Test Time-Off Request Submission

```bash
curl -X POST "http://localhost:5000/api/hr/time-off/request" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: tenant-1" \
  -d '{
    "employee_id": "EMP-001",
    "type": "vacation",
    "start_date": "2024-02-01",
    "end_date": "2024-02-07",
    "reason": "Family vacation",
    "emergency_contact": "+1-555-0123"
  }'
```

### Test Approval

```bash
curl -X POST "http://localhost:5000/api/hr/time-off/requests/REQ-001/approve" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <manager-token>" \
  -H "X-Tenant-ID: tenant-1" \
  -d '{
    "approved": true,
    "comments": "Approved!",
    "approved_by": "manager-123"
  }'
```

### Verify in Camunda Cockpit

1. Open http://localhost:8080/camunda/app/cockpit
2. Navigate to "Processes"
3. Click on "TimeOffApproval"
4. View running instances
5. Check process variables

## Error Handling

### Graceful Degradation

If Camunda is unavailable, the system continues to function:

```python
try:
    await CamundaClient.send_message(...)
except Exception as e:
    logger.error(f"Camunda unavailable: {str(e)}")
    # Save request to database anyway
    # Mark for manual processing
```

### Retry Logic

```python
# Automatic retries for transient failures
- Connection timeout: Retry 3 times
- 5xx errors: Retry 2 times
- Network errors: Retry 3 times
```

## Monitoring

### Metrics to Track

1. **Workflow Instances** - Total started, completed, failed
2. **Task Completion Time** - Average time to complete tasks
3. **Approval Rate** - Percentage of approved vs rejected
4. **SLA Compliance** - Requests processed within SLA
5. **Error Rate** - Failed Camunda API calls

### Logging

```python
# All Camunda interactions are logged
logger.info(f"Starting Camunda process: {process_key}")
logger.info(f"Process instance started: {process_instance_id}")
logger.info(f"Completing task: {task_id}")
logger.error(f"Failed to start Camunda process: {error}")
```

## Best Practices

1. **Use Business Keys** - For easy correlation
2. **Set Meaningful Variables** - For process visibility
3. **Handle Errors Gracefully** - Don't fail if Camunda is down
4. **Log All Interactions** - For debugging and auditing
5. **Use Tenant IDs** - For multi-tenancy support
6. **Version BPMN Models** - For backward compatibility
7. **Monitor Workflow Health** - Track completion rates
8. **Test Workflows** - Before deploying to production

## Security

### Authentication

```python
# Basic auth for Camunda REST API
headers = {
    "Authorization": f"Basic {base64_encode(user:password)}"
}
```

### Authorization

- Camunda task assignment based on roles
- ERP permission checks before task completion
- Tenant isolation in workflows

## Next Steps

1. ✅ Implement email notifications
2. ✅ Add calendar integration
3. ✅ Implement escalation rules
4. ✅ Add reporting and analytics
5. ✅ Implement SLA monitoring
6. ✅ Add mobile app support
7. ✅ Implement bulk approvals
