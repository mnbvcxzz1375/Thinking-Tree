"""Export/Import schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Any


class ExportOptions(BaseModel):
    """Options for data export."""

    include_activities: bool = Field(
        default=True, description="Include activities in export"
    )
    include_tree_nodes: bool = Field(
        default=True, description="Include tree nodes in export"
    )
    include_speech_records: bool = Field(
        default=False, description="Include speech records in export"
    )
    include_teacher_reviews: bool = Field(
        default=False, description="Include teacher reviews in export"
    )
    activity_ids: Optional[List[int]] = Field(
        None, description="Specific activity IDs to export"
    )


class ExportData(BaseModel):
    """Exported data structure."""

    version: str = Field(default="1.0", description="Export format version")
    exported_at: datetime = Field(
        default_factory=datetime.utcnow, description="Export timestamp"
    )
    activities: List[dict[str, Any]] = Field(default_factory=list)
    tree_nodes: List[dict[str, Any]] = Field(default_factory=list)
    speech_records: List[dict[str, Any]] = Field(default_factory=list)
    teacher_reviews: List[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ImportResult(BaseModel):
    """Import operation result."""

    success: bool
    activities_imported: int = 0
    tree_nodes_imported: int = 0
    speech_records_imported: int = 0
    teacher_reviews_imported: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ExportResponse(BaseModel):
    """Export endpoint response."""

    data: ExportData
    filename: str
    size_bytes: int


class HealthCheckResponse(BaseModel):
    """Database health check response."""

    status: str
    database_connected: bool
    pool_size: Optional[int] = None
    checked_out_connections: Optional[int] = None
    overflow: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
