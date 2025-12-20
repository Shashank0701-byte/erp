"""
Time-Off Request Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from enum import Enum


class TimeOffType(str, Enum):
    """Time-off request types"""
    VACATION = "vacation"
    SICK_LEAVE = "sick_leave"
    PERSONAL = "personal"
    BEREAVEMENT = "bereavement"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    UNPAID = "unpaid"


class TimeOffStatus(str, Enum):
    """Time-off request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TimeOffRequestCreate(BaseModel):
    """Schema for creating time-off request"""
    employee_id: str = Field(..., description="Employee ID requesting time off")
    type: TimeOffType = Field(..., description="Type of time off")
    start_date: date = Field(..., description="Start date of time off")
    end_date: date = Field(..., description="End date of time off")
    reason: str = Field(..., min_length=10, max_length=500, description="Reason for time off")
    emergency_contact: Optional[str] = Field(None, max_length=200, description="Emergency contact during leave")
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": "EMP-001",
                "type": "vacation",
                "start_date": "2024-02-01",
                "end_date": "2024-02-07",
                "reason": "Family vacation to Hawaii",
                "emergency_contact": "+1-555-0123"
            }
        }


class TimeOffRequestResponse(BaseModel):
    """Schema for time-off request response"""
    id: str
    employee_id: str
    employee_name: str
    type: TimeOffType
    start_date: date
    end_date: date
    days_requested: int
    reason: str
    status: TimeOffStatus
    submitted_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Camunda workflow information
    process_instance_id: Optional[str] = None
    current_task: Optional[str] = None
    
    class Config:
        from_attributes = True


class TimeOffApprovalDecision(BaseModel):
    """Schema for approving/rejecting time-off request"""
    approved: bool = Field(..., description="Whether to approve or reject")
    comments: Optional[str] = Field(None, max_length=500, description="Approval/rejection comments")
    approved_by: str = Field(..., description="User ID of approver")
    
    class Config:
        json_schema_extra = {
            "example": {
                "approved": True,
                "comments": "Approved. Enjoy your vacation!",
                "approved_by": "manager-123"
            }
        }


class CamundaProcessResponse(BaseModel):
    """Schema for Camunda process start response"""
    success: bool
    process_instance_id: str
    business_key: str
    message: str
    time_off_request_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "process_instance_id": "camunda-process-123",
                "business_key": "timeoff-REQ-001",
                "message": "Time-off approval workflow started successfully",
                "time_off_request_id": "REQ-001"
            }
        }
