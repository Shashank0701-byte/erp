from sqlalchemy import Column, String, Float, DateTime, Text, Index
from sqlalchemy.sql import func
from app.database import Base
import uuid


class JournalEntry(Base):
    """
    Journal Entry model for double-entry bookkeeping
    
    Attributes:
        id: Unique identifier
        tenant_id: Tenant identifier for multi-tenancy
        date: Transaction date
        description: Entry description
        reference: Optional reference number
        total_debit: Total debit amount
        total_credit: Total credit amount
        status: Entry status (draft, posted, approved, void)
        created_by: User ID who created the entry
        approved_by: User ID who approved the entry (optional)
        created_at: Timestamp when created
        updated_at: Timestamp when last updated
    """
    
    __tablename__ = "journal_entries"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: f"JE-{uuid.uuid4().hex[:12].upper()}")
    
    # Multi-tenancy
    tenant_id = Column(String, nullable=False, index=True)
    
    # Entry details
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    description = Column(Text, nullable=False)
    reference = Column(String(100), nullable=True)
    
    # Amounts
    total_debit = Column(Float, nullable=False)
    total_credit = Column(Float, nullable=False)
    
    # Status
    status = Column(String(20), nullable=False, default="draft", index=True)
    
    # Audit fields
    created_by = Column(String, nullable=False)
    approved_by = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_tenant_date', 'tenant_id', 'date'),
        Index('idx_tenant_status', 'tenant_id', 'status'),
        Index('idx_created_by', 'created_by'),
    )
    
    def __repr__(self):
        return f"<JournalEntry(id={self.id}, tenant={self.tenant_id}, amount={self.total_debit})>"
