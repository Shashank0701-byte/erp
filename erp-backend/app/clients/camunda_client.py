"""
Camunda BPM Client
Handles communication with Camunda workflow engine
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from app.utils.http_client import HTTPClient
from app.config import settings

logger = logging.getLogger(__name__)


class CamundaClient:
    """
    Client for communicating with Camunda BPM REST API
    
    Provides methods to start processes, complete tasks, and query workflow state
    """
    
    # Camunda REST API base URL (from environment or config)
    BASE_URL = getattr(settings, 'CAMUNDA_REST_URL', 'http://localhost:8080/engine-rest')
    
    @staticmethod
    async def start_process(
        process_definition_key: str,
        business_key: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a new process instance
        
        Args:
            process_definition_key: Key of the process definition (e.g., "TimeOffApproval")
            business_key: Optional business key for the process instance
            variables: Process variables as key-value pairs
            tenant_id: Optional tenant ID for multi-tenancy
            
        Returns:
            Dictionary with process instance information
            
        Example:
            {
                "id": "process-instance-id",
                "definitionId": "TimeOffApproval:1:deployment-id",
                "businessKey": "timeoff-123",
                "ended": false,
                "suspended": false,
                "tenantId": "tenant-1"
            }
        """
        url = f"{CamundaClient.BASE_URL}/process-definition/key/{process_definition_key}/start"
        
        # If tenant ID is provided, use tenant-specific endpoint
        if tenant_id:
            url = f"{CamundaClient.BASE_URL}/process-definition/key/{process_definition_key}/tenant-id/{tenant_id}/start"
        
        # Convert variables to Camunda format
        camunda_variables = {}
        if variables:
            for key, value in variables.items():
                camunda_variables[key] = CamundaClient._convert_to_camunda_variable(value)
        
        payload = {
            "variables": camunda_variables
        }
        
        if business_key:
            payload["businessKey"] = business_key
        
        try:
            logger.info(f"Starting Camunda process: {process_definition_key} with business key: {business_key}")
            
            response = await HTTPClient.post(url, json=payload)
            data = response.json()
            
            logger.info(f"Process instance started: {data.get('id')}")
            
            return data
        except Exception as e:
            logger.error(f"Failed to start Camunda process: {str(e)}")
            raise
    
    @staticmethod
    async def send_message(
        message_name: str,
        business_key: Optional[str] = None,
        process_variables: Optional[Dict[str, Any]] = None,
        correlation_keys: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to Camunda to trigger a message start event or intermediate catch event
        
        Args:
            message_name: Name of the message (e.g., "TimeOffRequestMessage")
            business_key: Optional business key
            process_variables: Variables to set in the process
            correlation_keys: Variables to correlate the message
            tenant_id: Optional tenant ID
            
        Returns:
            Dictionary with correlation result
            
        Example:
            {
                "resultType": "ProcessDefinition",
                "execution": null,
                "processInstance": {
                    "id": "process-instance-id",
                    "definitionId": "TimeOffApproval:1:deployment-id"
                }
            }
        """
        url = f"{CamundaClient.BASE_URL}/message"
        
        # Convert variables to Camunda format
        camunda_variables = {}
        if process_variables:
            for key, value in process_variables.items():
                camunda_variables[key] = CamundaClient._convert_to_camunda_variable(value)
        
        camunda_correlation = {}
        if correlation_keys:
            for key, value in correlation_keys.items():
                camunda_correlation[key] = CamundaClient._convert_to_camunda_variable(value)
        
        payload = {
            "messageName": message_name,
            "processVariables": camunda_variables
        }
        
        if business_key:
            payload["businessKey"] = business_key
        
        if correlation_keys:
            payload["correlationKeys"] = camunda_correlation
        
        if tenant_id:
            payload["tenantId"] = tenant_id
        
        try:
            logger.info(f"Sending message to Camunda: {message_name} with business key: {business_key}")
            
            response = await HTTPClient.post(url, json=payload)
            data = response.json()
            
            logger.info(f"Message sent successfully. Result type: {data.get('resultType')}")
            
            return data
        except Exception as e:
            logger.error(f"Failed to send Camunda message: {str(e)}")
            raise
    
    @staticmethod
    async def get_process_instance(
        process_instance_id: str
    ) -> Dict[str, Any]:
        """
        Get process instance details
        
        Args:
            process_instance_id: ID of the process instance
            
        Returns:
            Process instance information
        """
        url = f"{CamundaClient.BASE_URL}/process-instance/{process_instance_id}"
        
        try:
            response = await HTTPClient.get(url)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get process instance: {str(e)}")
            raise
    
    @staticmethod
    async def get_tasks(
        process_instance_id: Optional[str] = None,
        assignee: Optional[str] = None,
        candidate_user: Optional[str] = None,
        process_definition_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query tasks
        
        Args:
            process_instance_id: Filter by process instance
            assignee: Filter by assignee
            candidate_user: Filter by candidate user
            process_definition_key: Filter by process definition
            
        Returns:
            List of tasks
        """
        url = f"{CamundaClient.BASE_URL}/task"
        
        params = {}
        if process_instance_id:
            params["processInstanceId"] = process_instance_id
        if assignee:
            params["assignee"] = assignee
        if candidate_user:
            params["candidateUser"] = candidate_user
        if process_definition_key:
            params["processDefinitionKey"] = process_definition_key
        
        try:
            response = await HTTPClient.get(url, params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get tasks: {str(e)}")
            raise
    
    @staticmethod
    async def complete_task(
        task_id: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Complete a user task
        
        Args:
            task_id: ID of the task to complete
            variables: Variables to set when completing the task
        """
        url = f"{CamundaClient.BASE_URL}/task/{task_id}/complete"
        
        camunda_variables = {}
        if variables:
            for key, value in variables.items():
                camunda_variables[key] = CamundaClient._convert_to_camunda_variable(value)
        
        payload = {
            "variables": camunda_variables
        }
        
        try:
            logger.info(f"Completing task: {task_id}")
            await HTTPClient.post(url, json=payload)
            logger.info(f"Task completed: {task_id}")
        except Exception as e:
            logger.error(f"Failed to complete task: {str(e)}")
            raise
    
    @staticmethod
    async def get_process_variables(
        process_instance_id: str
    ) -> Dict[str, Any]:
        """
        Get all variables for a process instance
        
        Args:
            process_instance_id: ID of the process instance
            
        Returns:
            Dictionary of variables
        """
        url = f"{CamundaClient.BASE_URL}/process-instance/{process_instance_id}/variables"
        
        try:
            response = await HTTPClient.get(url)
            camunda_vars = response.json()
            
            # Convert from Camunda format to simple key-value pairs
            variables = {}
            for key, var_obj in camunda_vars.items():
                variables[key] = var_obj.get("value")
            
            return variables
        except Exception as e:
            logger.error(f"Failed to get process variables: {str(e)}")
            raise
    
    @staticmethod
    def _convert_to_camunda_variable(value: Any) -> Dict[str, Any]:
        """
        Convert Python value to Camunda variable format
        
        Args:
            value: Python value
            
        Returns:
            Camunda variable object
        """
        if isinstance(value, bool):
            return {"value": value, "type": "Boolean"}
        elif isinstance(value, int):
            return {"value": value, "type": "Integer"}
        elif isinstance(value, float):
            return {"value": value, "type": "Double"}
        elif isinstance(value, str):
            return {"value": value, "type": "String"}
        elif isinstance(value, datetime):
            return {"value": value.isoformat(), "type": "Date"}
        elif isinstance(value, dict):
            import json
            return {"value": json.dumps(value), "type": "Json"}
        elif isinstance(value, list):
            import json
            return {"value": json.dumps(value), "type": "Json"}
        else:
            return {"value": str(value), "type": "String"}
    
    @staticmethod
    async def delete_process_instance(
        process_instance_id: str,
        reason: Optional[str] = None
    ) -> None:
        """
        Delete (cancel) a process instance
        
        Args:
            process_instance_id: ID of the process instance
            reason: Optional reason for deletion
        """
        url = f"{CamundaClient.BASE_URL}/process-instance/{process_instance_id}"
        
        params = {}
        if reason:
            params["reason"] = reason
        
        try:
            logger.info(f"Deleting process instance: {process_instance_id}")
            await HTTPClient.delete(url, params=params)
            logger.info(f"Process instance deleted: {process_instance_id}")
        except Exception as e:
            logger.error(f"Failed to delete process instance: {str(e)}")
            raise
