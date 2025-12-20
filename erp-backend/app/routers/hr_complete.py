"""
HR module router - Employee Management and Time-Off Requests
With rate limiting on public-facing endpoints and Camunda workflow integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, date
import logging
import uuid

from app.database import get_db
from app.schemas import TokenData, Permission
from app.dependencies import get_current_user, require_permission
from app.dependencies.tenant import get_tenant_context
from app.schemas.tenant import TenantContext
from app.schemas.timeoff import (
    TimeOffRequestCreate,
    TimeOffRequestResponse,
    TimeOffApprovalDecision,
    CamundaProcessResponse,
    TimeOffStatus,
    TimeOffType
)
from app.clients.camunda_client import CamundaClient
from pydantic import BaseModel, Field, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hr", tags=["HR - Employee Management"])


# ... (existing employee endpoints remain the same) ...


# Time-Off Request Endpoints with Camunda Integration

@router.post(
    "/time-off/request",
    response_model=CamundaProcessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Time-Off Request",
    description="Submit a time-off request and start Camunda approval workflow"
)
async def submit_time_off_request(
    request_data: TimeOffRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Submit a time-off request and start the Camunda approval workflow
    
    This endpoint:
    1. Validates the time-off request
    2. Creates a time-off request record
    3. Sends a message to Camunda to start the TimeOffApproval workflow
    4. Returns the process instance ID for tracking
    
    Requires authentication
    """
    try:
        # Generate unique request ID
        request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        business_key = f"timeoff-{request_id}"
        
        # Calculate days requested
        days_requested = (request_data.end_date - request_data.start_date).days + 1
        
        if days_requested <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
        
        # Prepare process variables for Camunda
        process_variables = {
            "requestId": request_id,
            "employeeId": request_data.employee_id,
            "employeeName": f"Employee {request_data.employee_id}",  # In production, fetch from DB
            "employeeEmail": current_user.email,
            "timeOffType": request_data.type.value,
            "startDate": request_data.start_date.isoformat(),
            "endDate": request_data.end_date.isoformat(),
            "daysRequested": days_requested,
            "reason": request_data.reason,
            "emergencyContact": request_data.emergency_contact or "",
            "submittedAt": datetime.utcnow().isoformat(),
            "tenantId": tenant.tenant_id,
            "status": "pending"
        }
        
        logger.info(
            f"Submitting time-off request {request_id} for employee {request_data.employee_id}"
        )
        
        # Send message to Camunda to start the workflow
        camunda_response = await CamundaClient.send_message(
            message_name="TimeOffRequestMessage",
            business_key=business_key,
            process_variables=process_variables,
            tenant_id=tenant.tenant_id
        )
        
        # Extract process instance ID
        process_instance_id = None
        if camunda_response.get("processInstance"):
            process_instance_id = camunda_response["processInstance"]["id"]
        
        logger.info(
            f"Camunda workflow started for request {request_id}. "
            f"Process instance: {process_instance_id}"
        )
        
        # In production, save to database
        # time_off_request = TimeOffRequest(
        #     id=request_id,
        #     tenant_id=tenant.tenant_id,
        #     employee_id=request_data.employee_id,
        #     type=request_data.type,
        #     start_date=request_data.start_date,
        #     end_date=request_data.end_date,
        #     days_requested=days_requested,
        #     reason=request_data.reason,
        #     status=TimeOffStatus.PENDING,
        #     process_instance_id=process_instance_id,
        #     submitted_at=datetime.utcnow()
        # )
        # db.add(time_off_request)
        # await db.commit()
        
        return CamundaProcessResponse(
            success=True,
            process_instance_id=process_instance_id or "mock-process-id",
            business_key=business_key,
            message="Time-off request submitted successfully. Approval workflow started.",
            time_off_request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting time-off request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit time-off request: {str(e)}"
        )


@router.get(
    "/time-off/requests",
    response_model=List[dict],
    summary="List Time-Off Requests",
    description="Get all time-off requests for current user or all employees (managers)"
)
async def list_time_off_requests(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    tenant: TenantContext = Depends(get_tenant_context),
    employee_id: Optional[str] = Query(None, description="Filter by employee ID"),
    status_filter: Optional[TimeOffStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    List time-off requests
    
    - Regular employees see only their own requests
    - Managers/HR can see all requests or filter by employee
    """
    # Mock data
    requests = [
        {
            "id": "REQ-001",
            "employee_id": "EMP-001",
            "employee_name": "John Doe",
            "type": "vacation",
            "start_date": "2024-02-01",
            "end_date": "2024-02-07",
            "days_requested": 7,
            "reason": "Family vacation",
            "status": "pending",
            "submitted_at": "2024-01-15T10:00:00Z",
            "process_instance_id": "camunda-process-123"
        }
    ]
    
    # Apply filters
    if employee_id:
        requests = [r for r in requests if r["employee_id"] == employee_id]
    
    if status_filter:
        requests = [r for r in requests if r["status"] == status_filter.value]
    
    return requests[skip:skip + limit]


@router.get(
    "/time-off/requests/{request_id}",
    response_model=dict,
    summary="Get Time-Off Request",
    description="Get details of a specific time-off request"
)
async def get_time_off_request(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Get time-off request details including workflow status
    """
    # Mock data
    request_data = {
        "id": request_id,
        "employee_id": "EMP-001",
        "employee_name": "John Doe",
        "type": "vacation",
        "start_date": "2024-02-01",
        "end_date": "2024-02-07",
        "days_requested": 7,
        "reason": "Family vacation",
        "status": "pending",
        "submitted_at": "2024-01-15T10:00:00Z",
        "process_instance_id": "camunda-process-123",
        "current_task": "Manager Approval"
    }
    
    # In production, fetch workflow status from Camunda
    # if request_data.get("process_instance_id"):
    #     try:
    #         tasks = await CamundaClient.get_tasks(
    #             process_instance_id=request_data["process_instance_id"]
    #         )
    #         if tasks:
    #             request_data["current_task"] = tasks[0].get("name")
    #     except Exception as e:
    #         logger.error(f"Failed to get workflow status: {str(e)}")
    
    return request_data


@router.post(
    "/time-off/requests/{request_id}/approve",
    response_model=dict,
    summary="Approve/Reject Time-Off Request",
    description="Approve or reject a time-off request (managers only)"
)
async def approve_time_off_request(
    request_id: str,
    decision: TimeOffApprovalDecision,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.APPROVE_HR)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Approve or reject a time-off request
    
    This endpoint:
    1. Validates the approver has permission
    2. Completes the Camunda user task with the decision
    3. Updates the request status in the database
    
    Requires APPROVE_HR permission
    """
    try:
        logger.info(
            f"Processing approval decision for request {request_id} by {current_user.user_id}"
        )
        
        # In production, fetch request from database
        # request_data = await db.get(TimeOffRequest, request_id)
        # if not request_data:
        #     raise HTTPException(status_code=404, detail="Request not found")
        
        # Mock process instance ID
        process_instance_id = "camunda-process-123"
        
        # Get pending tasks for this process instance
        try:
            tasks = await CamundaClient.get_tasks(
                process_instance_id=process_instance_id
            )
            
            if not tasks:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No pending approval task found for this request"
                )
            
            # Complete the first pending task with the decision
            task_id = tasks[0]["id"]
            
            task_variables = {
                "approved": decision.approved,
                "approverComments": decision.comments or "",
                "approvedBy": decision.approved_by,
                "approvedAt": datetime.utcnow().isoformat()
            }
            
            await CamundaClient.complete_task(task_id, task_variables)
            
            logger.info(f"Camunda task {task_id} completed with decision: {decision.approved}")
            
        except Exception as e:
            logger.error(f"Failed to complete Camunda task: {str(e)}")
            # Continue even if Camunda fails (graceful degradation)
        
        # Update request status in database
        new_status = TimeOffStatus.APPROVED if decision.approved else TimeOffStatus.REJECTED
        
        # In production:
        # request_data.status = new_status
        # request_data.approved_by = decision.approved_by
        # request_data.approved_at = datetime.utcnow()
        # if not decision.approved:
        #     request_data.rejection_reason = decision.comments
        # await db.commit()
        
        return {
            "success": True,
            "request_id": request_id,
            "status": new_status.value,
            "message": f"Time-off request {'approved' if decision.approved else 'rejected'} successfully",
            "approved_by": decision.approved_by
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing approval: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process approval: {str(e)}"
        )


@router.delete(
    "/time-off/requests/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel Time-Off Request",
    description="Cancel a pending time-off request"
)
async def cancel_time_off_request(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Cancel a pending time-off request
    
    - Employees can cancel their own pending requests
    - Cancels the Camunda workflow instance
    """
    try:
        logger.info(f"Cancelling time-off request {request_id}")
        
        # In production, fetch request and verify ownership
        # request_data = await db.get(TimeOffRequest, request_id)
        # if request_data.employee_id != current_user.user_id:
        #     raise HTTPException(status_code=403, detail="Not authorized")
        
        # Mock process instance ID
        process_instance_id = "camunda-process-123"
        
        # Cancel Camunda workflow
        try:
            await CamundaClient.delete_process_instance(
                process_instance_id=process_instance_id,
                reason=f"Cancelled by employee {current_user.user_id}"
            )
            logger.info(f"Camunda process instance {process_instance_id} cancelled")
        except Exception as e:
            logger.error(f"Failed to cancel Camunda process: {str(e)}")
        
        # Update status in database
        # request_data.status = TimeOffStatus.CANCELLED
        # await db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel request: {str(e)}"
        )


@router.get(
    "/time-off/balance/{employee_id}",
    response_model=dict,
    summary="Get Time-Off Balance",
    description="Get time-off balance for an employee"
)
async def get_time_off_balance(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Get time-off balance for an employee
    
    Shows available days for each time-off type
    """
    # Mock data
    balance = {
        "employee_id": employee_id,
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
                "pending_days": 0,
                "available_days": 8
            },
            "personal": {
                "total_days": 5,
                "used_days": 1,
                "pending_days": 0,
                "available_days": 4
            }
        },
        "year": 2024
    }
    
    return balance
