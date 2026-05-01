"""Data export/import router with multi-format export support."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db, check_db_health, get_engine
from app.services.data_service import DataService
from app.services.export_service import ExportService
from app.schemas.export import (
    ExportOptions,
    ExportResponse,
    ImportResult,
    HealthCheckResponse,
)
from datetime import datetime, timezone

router = APIRouter()


# ── Request/Response schemas ──────────────────────────────────────────


class SvgExportRequest(BaseModel):
    """Request body for SVG-based exports."""

    svg_data: str = Field(..., description="SVG markup string")
    scale: float = Field(default=2.0, ge=0.5, le=4.0, description="Resolution scale")


class MarkdownExportRequest(BaseModel):
    """Request body for Markdown export."""

    include_metadata: bool = Field(
        default=True, description="Include timestamps and metadata"
    )


class ExportSizeEstimate(BaseModel):
    """Export size estimate response."""

    format: str
    node_count: int
    estimated_size_kb: float
    estimated_size_mb: float
    max_size_mb: float
    within_limit: bool


class SvgValidationResponse(BaseModel):
    """SVG validation response."""

    valid: bool
    error: str | None = None


@router.post("/export", response_model=ExportResponse)
async def export_data(
    options: ExportOptions,
    db: Session = Depends(get_db),
) -> ExportResponse:
    """Export data from database."""
    try:
        export_result = DataService.export_data(db, options)
        json_str = DataService.export_to_json(export_result)

        filename = f"thinking_tree_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

        return ExportResponse(
            data=export_result,
            filename=filename,
            size_bytes=len(json_str.encode("utf-8")),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}",
        )


@router.post("/import", response_model=ImportResult)
async def import_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ImportResult:
    """Import data from JSON file."""
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JSON files are supported",
        )

    try:
        content = await file.read()
        json_str = content.decode("utf-8")
        export_data = DataService.import_from_json(json_str)
        result = DataService.import_data(db, export_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Import failed: {str(e)}",
        )


# ── Multi-format export endpoints ─────────────────────────────────────


@router.post("/export/png")
async def export_as_png(request: SvgExportRequest) -> Response:
    """Export tree visualization as PNG image.

    Accepts SVG data and converts to high-resolution PNG.
    """
    # Validate SVG
    is_valid, error = ExportService.validate_svg(request.svg_data)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid SVG: {error}",
        )

    try:
        png_bytes = ExportService.svg_to_png(request.svg_data, scale=request.scale)

        # Check size limit (10 MB)
        if len(png_bytes) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="PNG output exceeds 10 MB limit",
            )

        filename = f"thinking_tree_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.png"

        return Response(
            content=png_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(png_bytes)),
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/export/pdf")
async def export_as_pdf(
    request: SvgExportRequest,
    title: str = "Thinking Tree",
) -> Response:
    """Export tree visualization as PDF document.

    Accepts SVG data and converts to PDF with title and metadata.
    """
    is_valid, error = ExportService.validate_svg(request.svg_data)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid SVG: {error}",
        )

    try:
        pdf_bytes = ExportService.svg_to_pdf(request.svg_data, title=title)

        filename = f"thinking_tree_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/export/markdown/{activity_id}")
async def export_as_markdown(
    activity_id: int,
    include_metadata: bool = True,
    db: Session = Depends(get_db),
) -> Response:
    """Export tree as Markdown document.

    Generates a structured Markdown file from the tree data.
    """
    try:
        md_content = ExportService.tree_to_markdown(
            db, activity_id, include_metadata=include_metadata
        )

        filename = f"thinking_tree_{activity_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"

        return Response(
            content=md_content.encode("utf-8"),
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/export/json/{activity_id}")
async def export_as_json(
    activity_id: int,
    pretty: bool = True,
    db: Session = Depends(get_db),
) -> Response:
    """Export tree as formatted JSON.

    Generates a structured JSON file from the tree data.
    """
    try:
        json_content = ExportService.tree_to_json(db, activity_id, pretty=pretty)

        filename = f"thinking_tree_{activity_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

        return Response(
            content=json_content.encode("utf-8"),
            media_type="application/json; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/export/validate-svg", response_model=SvgValidationResponse)
async def validate_svg(request: SvgExportRequest) -> SvgValidationResponse:
    """Validate SVG data before export."""
    is_valid, error = ExportService.validate_svg(request.svg_data)
    return SvgValidationResponse(valid=is_valid, error=error)


@router.get(
    "/export/size-estimate/{format_type}/{node_count}",
    response_model=ExportSizeEstimate,
)
async def get_size_estimate(
    format_type: str,
    node_count: int,
) -> ExportSizeEstimate:
    """Estimate export file size for given format and node count."""
    if format_type not in ("png", "pdf", "markdown", "json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {format_type}. Use png, pdf, markdown, or json.",
        )

    estimate = ExportService.get_export_size_estimate(format_type, node_count)
    return ExportSizeEstimate(**estimate)


@router.get("/health", response_model=HealthCheckResponse)
async def database_health() -> HealthCheckResponse:
    """Check database health and connection pool status."""
    db_connected = check_db_health()

    pool_size = None
    checked_out = None
    overflow = None

    if db_connected:
        try:
            engine = get_engine()
            pool = engine.pool
            pool_size = pool.size()
            checked_out = pool.checkedout()
            overflow = pool.overflow()
        except Exception:
            pass

    return HealthCheckResponse(
        status="healthy" if db_connected else "unhealthy",
        database_connected=db_connected,
        pool_size=pool_size,
        checked_out_connections=checked_out,
        overflow=overflow,
    )
