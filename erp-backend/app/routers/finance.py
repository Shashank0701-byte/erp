"""
Finance module router - Journal Entries
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
import logging

from app.database import get_db
from app.models.journal_entry import JournalEntry
from app.schemas import (
    JournalEntryCreate,
    JournalEntryResponse,
    JournalEntryUpdate,
    TokenData,
    Permission
)
from app.dependencies import get_current_user, require_permission
from app.dependencies.tenant import get_tenant_context
from app.schemas.tenant import TenantContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/finance", tags=["Finance - Journal Entries"])


@router.post(
    "/journal-entries",
    response_model=JournalEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Journal Entry",
    description="Create a new journal entry with double-entry bookkeeping validation"
)
async def create_journal_entry(
    entry_data: JournalEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.CREATE_FINANCE)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Create a new journal entry
    
    This endpoint:
    1. Validates the journal entry data (debit = credit)
    2. Ensures user has CREATE_FINANCE permission
    3. Scopes entry to current tenant
    4. Stores entry in database using async SQLAlchemy
    5. Returns the created entry
    
    Args:
        entry_data: Journal entry creation data
        db: Database session
        current_user: Authenticated user with CREATE_FINANCE permission
        tenant: Current tenant context
        
    Returns:
        Created journal entry
        
    Raises:
        HTTPException 400: If validation fails
        HTTPException 403: If user lacks permission
        HTTPException 500: If database error occurs
    """
    try:
        logger.info(
            f"Creating journal entry for tenant {tenant.tenant_id} "
            f"by user {current_user.user_id}"
        )
        
        # Validate debit = credit (already validated by Pydantic, but double-check)
        if abs(entry_data.total_debit - entry_data.total_credit) > 0.01:
            logger.warning(
                f"Journal entry validation failed: "
                f"debit={entry_data.total_debit}, credit={entry_data.total_credit}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total debit must equal total credit"
            )
        
        # Create journal entry model
        journal_entry = JournalEntry(
            tenant_id=tenant.tenant_id,
            date=entry_data.date,
            description=entry_data.description,
            reference=entry_data.reference,
            total_debit=entry_data.total_debit,
            total_credit=entry_data.total_credit,
            status="draft",  # New entries start as draft
            created_by=current_user.user_id
        )
        
        # Add to database
        db.add(journal_entry)
        
        # Commit transaction
        await db.commit()
        
        # Refresh to get generated fields
        await db.refresh(journal_entry)
        
        logger.info(
            f"Journal entry created successfully: {journal_entry.id} "
            f"for tenant {tenant.tenant_id}"
        )
        
        # Return response
        return JournalEntryResponse(
            id=journal_entry.id,
            date=journal_entry.date,
            description=journal_entry.description,
            reference=journal_entry.reference,
            total_debit=journal_entry.total_debit,
            total_credit=journal_entry.total_credit,
            status=journal_entry.status,
            created_by=journal_entry.created_by,
            created_at=journal_entry.created_at,
            updated_at=journal_entry.updated_at
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Rollback on error
        await db.rollback()
        logger.error(
            f"Error creating journal entry: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create journal entry: {str(e)}"
        )


@router.get(
    "/journal-entries",
    response_model=List[JournalEntryResponse],
    summary="List Journal Entries",
    description="Get all journal entries for current tenant"
)
async def list_journal_entries(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.VIEW_FINANCE)),
    tenant: TenantContext = Depends(get_tenant_context),
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None
):
    """
    List journal entries for current tenant
    
    Args:
        db: Database session
        current_user: Authenticated user with VIEW_FINANCE permission
        tenant: Current tenant context
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        status_filter: Optional status filter (draft, posted, approved, void)
        
    Returns:
        List of journal entries
    """
    try:
        logger.info(f"Listing journal entries for tenant {tenant.tenant_id}")
        
        # Build query
        query = select(JournalEntry).where(
            JournalEntry.tenant_id == tenant.tenant_id
        )
        
        # Apply status filter if provided
        if status_filter:
            query = query.where(JournalEntry.status == status_filter)
        
        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(JournalEntry.date.desc())
        
        # Execute query
        result = await db.execute(query)
        entries = result.scalars().all()
        
        logger.info(f"Found {len(entries)} journal entries for tenant {tenant.tenant_id}")
        
        # Convert to response models
        return [
            JournalEntryResponse(
                id=entry.id,
                date=entry.date,
                description=entry.description,
                reference=entry.reference,
                total_debit=entry.total_debit,
                total_credit=entry.total_credit,
                status=entry.status,
                created_by=entry.created_by,
                created_at=entry.created_at,
                updated_at=entry.updated_at
            )
            for entry in entries
        ]
        
    except Exception as e:
        logger.error(f"Error listing journal entries: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve journal entries: {str(e)}"
        )


@router.get(
    "/journal-entries/{entry_id}",
    response_model=JournalEntryResponse,
    summary="Get Journal Entry",
    description="Get a specific journal entry by ID"
)
async def get_journal_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.VIEW_FINANCE)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Get a specific journal entry
    
    Args:
        entry_id: Journal entry ID
        db: Database session
        current_user: Authenticated user with VIEW_FINANCE permission
        tenant: Current tenant context
        
    Returns:
        Journal entry details
        
    Raises:
        HTTPException 404: If entry not found or doesn't belong to tenant
    """
    try:
        # Query with tenant isolation
        query = select(JournalEntry).where(
            and_(
                JournalEntry.id == entry_id,
                JournalEntry.tenant_id == tenant.tenant_id
            )
        )
        
        result = await db.execute(query)
        entry = result.scalar_one_or_none()
        
        if not entry:
            logger.warning(
                f"Journal entry {entry_id} not found for tenant {tenant.tenant_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Journal entry {entry_id} not found"
            )
        
        return JournalEntryResponse(
            id=entry.id,
            date=entry.date,
            description=entry.description,
            reference=entry.reference,
            total_debit=entry.total_debit,
            total_credit=entry.total_credit,
            status=entry.status,
            created_by=entry.created_by,
            created_at=entry.created_at,
            updated_at=entry.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving journal entry: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve journal entry: {str(e)}"
        )


@router.put(
    "/journal-entries/{entry_id}",
    response_model=JournalEntryResponse,
    summary="Update Journal Entry",
    description="Update an existing journal entry"
)
async def update_journal_entry(
    entry_id: str,
    entry_data: JournalEntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.EDIT_FINANCE)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Update a journal entry
    
    Only draft entries can be updated
    """
    try:
        # Get existing entry
        query = select(JournalEntry).where(
            and_(
                JournalEntry.id == entry_id,
                JournalEntry.tenant_id == tenant.tenant_id
            )
        )
        
        result = await db.execute(query)
        entry = result.scalar_one_or_none()
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Journal entry {entry_id} not found"
            )
        
        # Only allow updating draft entries
        if entry.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update {entry.status} entry. Only draft entries can be updated."
            )
        
        # Update fields
        update_data = entry_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)
        
        # Validate debit = credit if amounts are updated
        if abs(entry.total_debit - entry.total_credit) > 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total debit must equal total credit"
            )
        
        await db.commit()
        await db.refresh(entry)
        
        logger.info(f"Journal entry {entry_id} updated successfully")
        
        return JournalEntryResponse(
            id=entry.id,
            date=entry.date,
            description=entry.description,
            reference=entry.reference,
            total_debit=entry.total_debit,
            total_credit=entry.total_credit,
            status=entry.status,
            created_by=entry.created_by,
            created_at=entry.created_at,
            updated_at=entry.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating journal entry: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update journal entry: {str(e)}"
        )


@router.delete(
    "/journal-entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Journal Entry",
    description="Delete a journal entry (soft delete by setting status to void)"
)
async def delete_journal_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.DELETE_FINANCE)),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Delete (void) a journal entry
    
    This performs a soft delete by setting status to 'void'
    """
    try:
        query = select(JournalEntry).where(
            and_(
                JournalEntry.id == entry_id,
                JournalEntry.tenant_id == tenant.tenant_id
            )
        )
        
        result = await db.execute(query)
        entry = result.scalar_one_or_none()
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Journal entry {entry_id} not found"
            )
        
        # Soft delete - set status to void
        entry.status = "void"
        
        await db.commit()
        
        logger.info(f"Journal entry {entry_id} voided successfully")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting journal entry: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete journal entry: {str(e)}"
        )
