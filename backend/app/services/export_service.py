"""Export service for generating tree visualizations in multiple formats."""
from __future__ import annotations

import io
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any
from xml.etree import ElementTree

from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.tree_node import TreeNode
from app.schemas.export import ExportData, ExportOptions

logger = logging.getLogger(__name__)

# File size limits
MAX_SVG_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_EXPORT_NODES = 5000


class ExportService:
    """Service for exporting tree data in various formats."""

    # ── PNG Export ────────────────────────────────────────────────────

    @staticmethod
    def svg_to_png(svg_data: str, scale: float = 2.0) -> bytes:
        """Convert SVG string to PNG bytes using cairosvg.

        Args:
            svg_data: Raw SVG markup string
            scale: Resolution scale factor (1.0 = 72 DPI, 2.0 = 144 DPI)

        Returns:
            PNG image bytes

        Raises:
            ValueError: If SVG is invalid or too large
            RuntimeError: If conversion fails
        """
        if len(svg_data.encode("utf-8")) > MAX_SVG_SIZE_BYTES:
            raise ValueError(
                f"SVG data exceeds maximum size of {MAX_SVG_SIZE_BYTES // (1024 * 1024)} MB"
            )

        # Validate SVG structure
        try:
            ElementTree.fromstring(svg_data)
        except ElementTree.ParseError as e:
            raise ValueError(f"Invalid SVG data: {e}")

        try:
            import cairosvg  # type: ignore[import-untyped]

            png_bytes = cairosvg.svg2png(  # type: ignore[no-untyped-call]
                bytestring=svg_data.encode("utf-8"),
                scale=scale,
                output_width=None,
                output_height=None,
            )
            return png_bytes
        except ImportError:
            logger.warning("cairosvg not installed, using fallback PNG generation")
            return ExportService._svg_to_png_fallback(svg_data, scale)
        except Exception as e:
            raise RuntimeError(f"PNG conversion failed: {e}")

    @staticmethod
    def _svg_to_png_fallback(svg_data: str, scale: float = 2.0) -> bytes:
        """Fallback PNG generation using Pillow with SVG parsing.

        Creates a simple PNG representation when cairosvg is unavailable.
        """
        try:
            from PIL import Image, ImageDraw

            # Parse SVG dimensions
            width, height = ExportService._parse_svg_dimensions(svg_data)
            width = int(width * scale)
            height = int(height * scale)

            # Create image with white background
            img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
            draw = ImageDraw.Draw(img)

            # Draw tree structure from SVG paths
            ExportService._draw_svg_content(draw, svg_data, scale)

            # Convert to PNG bytes
            buffer = io.BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            return buffer.getvalue()
        except ImportError:
            raise RuntimeError(
                "Neither cairosvg nor Pillow is installed. "
                "Install with: pip install cairosvg or pip install Pillow"
            )

    @staticmethod
    def _parse_svg_dimensions(svg_data: str) -> tuple[float, float]:
        """Parse width and height from SVG element."""
        try:
            root = ElementTree.fromstring(svg_data)
            width = root.get("width", "800")
            height = root.get("height", "600")

            # Handle viewBox if width/height are percentages
            if "%" in str(width) or "%" in str(height):
                viewBox = root.get("viewBox", "0 0 800 600")
                parts = viewBox.split()
                if len(parts) == 4:
                    width = parts[2]
                    height = parts[3]

            # Strip non-numeric characters
            width = re.sub(r"[^0-9.]", "", str(width)) or "800"
            height = re.sub(r"[^0-9.]", "", str(height)) or "600"

            return float(width), float(height)
        except Exception:
            return 800.0, 600.0

    @staticmethod
    def _draw_svg_content(draw: Any, svg_data: str, scale: float) -> None:
        """Draw basic SVG content onto a Pillow ImageDraw."""
        try:
            root = ElementTree.fromstring(svg_data)

            # Draw circles (tree nodes)
            for circle in root.iter("{http://www.w3.org/2000/svg}circle"):
                cx = float(circle.get("cx", 0)) * scale
                cy = float(circle.get("cy", 0)) * scale
                r = float(circle.get("r", 10)) * scale
                fill = circle.get("fill", "#4CAF50")
                color = ExportService._parse_color(fill)
                draw.ellipse(
                    [cx - r, cy - r, cx + r, cy + r],
                    fill=color,
                    outline=(0, 0, 0),
                )

            # Draw text elements
            for text_elem in root.iter("{http://www.w3.org/2000/svg}text"):
                x = float(text_elem.get("x", 0)) * scale
                y = float(text_elem.get("y", 0)) * scale
                text = text_elem.text or ""
                if text:
                    draw.text((x, y), text, fill=(0, 0, 0))

        except Exception as e:
            logger.warning(f"Failed to draw SVG content: {e}")

    @staticmethod
    def _parse_color(color_str: str) -> tuple[int, int, int]:
        """Parse CSS color string to RGB tuple."""
        color_map = {
            "#4CAF50": (76, 175, 80),
            "#66BB6A": (102, 187, 106),
            "#81C784": (129, 199, 132),
            "#43A047": (67, 160, 71),
            "#FFCA28": (255, 202, 40),
            "#795548": (121, 85, 72),
        }
        if color_str in color_map:
            return color_map[color_str]

        # Try hex parsing
        if color_str.startswith("#") and len(color_str) == 7:
            try:
                r = int(color_str[1:3], 16)
                g = int(color_str[3:5], 16)
                b = int(color_str[5:7], 16)
                return (r, g, b)
            except ValueError:
                pass

        return (76, 175, 80)  # Default green

    # ── PDF Export ────────────────────────────────────────────────────

    @staticmethod
    def svg_to_pdf(svg_data: str, title: str = "Thinking Tree") -> bytes:
        """Convert SVG to PDF document.

        Args:
            svg_data: Raw SVG markup string
            title: Document title

        Returns:
            PDF document bytes

        Raises:
            ValueError: If SVG is invalid
            RuntimeError: If conversion fails
        """
        if len(svg_data.encode("utf-8")) > MAX_SVG_SIZE_BYTES:
            raise ValueError("SVG data exceeds maximum size limit")

        try:
            import cairosvg  # type: ignore[import-untyped]

            pdf_bytes = cairosvg.svg2pdf(  # type: ignore[no-untyped-call]
                bytestring=svg_data.encode("utf-8"),
            )
            return pdf_bytes
        except ImportError:
            logger.warning("cairosvg not installed, using reportlab fallback")
            return ExportService._svg_to_pdf_fallback(svg_data, title)
        except Exception as e:
            raise RuntimeError(f"PDF conversion failed: {e}")

    @staticmethod
    def _svg_to_pdf_fallback(svg_data: str, title: str) -> bytes:
        """Fallback PDF generation using reportlab."""
        try:
            from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
            from reportlab.lib.units import inch  # type: ignore[import-untyped]
            from reportlab.pdfgen import canvas as pdf_canvas  # type: ignore[import-untyped]

            width, height = ExportService._parse_svg_dimensions(svg_data)
            buffer = io.BytesIO()

            c = pdf_canvas.Canvas(buffer, pagesize=A4)
            page_width, page_height = A4

            # Add title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(
                inch, page_height - inch, title
            )

            # Add timestamp
            c.setFont("Helvetica", 10)
            c.drawString(
                inch,
                page_height - inch - 20,
                f"Exported: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            )

            # Scale SVG to fit page
            scale_x = (page_width - 2 * inch) / width
            scale_y = (page_height - 3 * inch) / height
            scale = min(scale_x, scale_y)

            # Draw basic tree representation
            c.setFont("Helvetica", 8)
            y_offset = page_height - 2.5 * inch

            root = ElementTree.fromstring(svg_data)
            for text_elem in root.iter("{http://www.w3.org/2000/svg}text"):
                text = text_elem.text or ""
                if text and y_offset > inch:
                    c.drawString(inch, y_offset, text[:80])
                    y_offset -= 14

            c.save()
            return buffer.getvalue()
        except ImportError:
            raise RuntimeError(
                "Neither cairosvg nor reportlab is installed. "
                "Install with: pip install cairosvg or pip install reportlab"
            )

    # ── Markdown Export ───────────────────────────────────────────────

    @staticmethod
    def tree_to_markdown(
        db: Session,
        activity_id: int,
        include_metadata: bool = True,
    ) -> str:
        """Export tree as structured Markdown document.

        Args:
            db: Database session
            activity_id: Activity ID to export
            include_metadata: Include timestamps and metadata

        Returns:
            Markdown formatted string
        """
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise ValueError(f"Activity {activity_id} not found")

        nodes = (
            db.query(TreeNode)
            .filter(TreeNode.activity_id == activity_id)
            .all()
        )

        if len(nodes) > MAX_EXPORT_NODES:
            raise ValueError(
                f"Tree has {len(nodes)} nodes, exceeding limit of {MAX_EXPORT_NODES}"
            )

        lines: list[str] = []

        # Header
        lines.append(f"# {activity.title}")
        lines.append("")

        if activity.description:
            lines.append(f"> {activity.description}")
            lines.append("")

        if include_metadata:
            lines.append("---")
            lines.append(f"- **Difficulty**: {activity.difficulty_level}")
            if activity.age_group:
                lines.append(f"- **Age Group**: {activity.age_group}")
            lines.append(
                f"- **Exported**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            )
            lines.append(f"- **Total Nodes**: {len(nodes)}")
            lines.append("---")
            lines.append("")

        # Build tree structure
        node_map: dict[int, dict] = {}
        roots: list[int] = []

        for node in nodes:
            node_map[node.id] = {
                "id": node.id,
                "content": node.content,
                "node_type": node.node_type,
                "parent_id": node.parent_id,
                "children": [],
            }

        for node in nodes:
            if node.parent_id and node.parent_id in node_map:
                node_map[node.parent_id]["children"].append(node.id)
            else:
                roots.append(node.id)

        # Render tree as nested Markdown
        lines.append("## Thinking Tree")
        lines.append("")

        type_icons = {
            "root": "🌳",
            "question": "❓",
            "answer": "💡",
            "insight": "✨",
            "branch": "🌿",
        }

        def render_node(node_id: int, depth: int = 0) -> None:
            node = node_map[node_id]
            indent = "  " * depth
            icon = type_icons.get(node["node_type"], "•")
            lines.append(f"{indent}- {icon} **{node['content']}**")

            if include_metadata and node["node_type"]:
                lines.append(f"{indent}  *({node['node_type']})*")

            for child_id in node["children"]:
                render_node(child_id, depth + 1)

        for root_id in roots:
            render_node(root_id)

        lines.append("")
        lines.append("---")
        lines.append(
            "*Generated by Children's Thinking Tree System*"
        )

        return "\n".join(lines)

    @staticmethod
    def data_to_markdown(export_data: ExportData) -> str:
        """Convert export data structure to Markdown.

        Args:
            export_data: Exported data from DataService

        Returns:
            Markdown formatted string
        """
        lines: list[str] = []

        lines.append("# Thinking Tree Export")
        lines.append("")
        lines.append(f"**Exported**: {export_data.exported_at.strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append(f"**Version**: {export_data.version}")
        lines.append("")

        # Activities
        if export_data.activities:
            lines.append("## Activities")
            lines.append("")
            for activity in export_data.activities:
                lines.append(f"### {activity.get('title', 'Untitled')}")
                if activity.get("description"):
                    lines.append(f"> {activity['description']}")
                lines.append("")
                lines.append(f"- **Difficulty**: {activity.get('difficulty_level', 'N/A')}")
                lines.append(f"- **Age Group**: {activity.get('age_group', 'N/A')}")
                lines.append("")

        # Tree Nodes
        if export_data.tree_nodes:
            lines.append("## Tree Nodes")
            lines.append("")
            lines.append(f"Total nodes: {len(export_data.tree_nodes)}")
            lines.append("")

            # Group by activity
            activity_nodes: dict[int, list[dict]] = {}
            for node in export_data.tree_nodes:
                aid = node.get("activity_id", 0)
                if aid not in activity_nodes:
                    activity_nodes[aid] = []
                activity_nodes[aid].append(node)

            for aid, nodes in activity_nodes.items():
                lines.append(f"### Activity {aid}")
                lines.append("")
                lines.append("| ID | Type | Content | Parent |")
                lines.append("|---:|------|---------|-------:|")
                for node in nodes:
                    parent = node.get("parent_id", "-") or "-"
                    lines.append(
                        f"| {node['id']} | {node.get('node_type', '?')} "
                        f"| {node.get('content', '')[:50]} | {parent} |"
                    )
                lines.append("")

        lines.append("---")
        lines.append("*Generated by Children's Thinking Tree System*")

        return "\n".join(lines)

    # ── JSON Export ───────────────────────────────────────────────────

    @staticmethod
    def tree_to_json(
        db: Session,
        activity_id: int,
        pretty: bool = True,
    ) -> str:
        """Export tree as formatted JSON string.

        Args:
            db: Database session
            activity_id: Activity ID to export
            pretty: Pretty-print JSON

        Returns:
            JSON string
        """
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise ValueError(f"Activity {activity_id} not found")

        nodes = (
            db.query(TreeNode)
            .filter(TreeNode.activity_id == activity_id)
            .all()
        )

        # Build nested tree
        node_map: dict[int, dict] = {}
        roots: list[dict] = []

        for node in nodes:
            node_map[node.id] = {
                "id": node.id,
                "content": node.content,
                "node_type": node.node_type,
                "position_x": node.position_x,
                "position_y": node.position_y,
                "created_at": node.created_at.isoformat() if node.created_at else None,
                "updated_at": node.updated_at.isoformat() if node.updated_at else None,
                "children": [],
            }

        for node in nodes:
            entry = node_map[node.id]
            if node.parent_id and node.parent_id in node_map:
                node_map[node.parent_id]["children"].append(entry)
            else:
                roots.append(entry)

        export = {
            "version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "activity": {
                "id": activity.id,
                "title": activity.title,
                "description": activity.description,
                "difficulty_level": activity.difficulty_level,
                "age_group": activity.age_group,
            },
            "tree": roots,
            "node_count": len(nodes),
        }

        indent = 2 if pretty else None
        return json.dumps(export, indent=indent, ensure_ascii=False)

    # ── Validation ────────────────────────────────────────────────────

    @staticmethod
    def validate_svg(svg_data: str) -> tuple[bool, str | None]:
        """Validate SVG data for export.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not svg_data or not svg_data.strip():
            return False, "SVG data is empty"

        size = len(svg_data.encode("utf-8"))
        if size > MAX_SVG_SIZE_BYTES:
            return (
                False,
                f"SVG size ({size // 1024} KB) exceeds limit ({MAX_SVG_SIZE_BYTES // 1024} KB)",
            )

        try:
            root = ElementTree.fromstring(svg_data)
            if root.tag != "{http://www.w3.org/2000/svg}svg" and root.tag != "svg":
                return False, "Root element is not an SVG element"
        except ElementTree.ParseError as e:
            return False, f"Invalid XML/SVG: {e}"

        return True, None

    @staticmethod
    def get_export_size_estimate(format_type: str, node_count: int) -> dict[str, Any]:
        """Estimate export file size.

        Args:
            format_type: Export format (png, pdf, markdown, json)
            node_count: Number of tree nodes

        Returns:
            Dict with size estimate info
        """
        estimates = {
            "png": {
                "base_kb": 50,
                "per_node_kb": 0.5,
                "max_mb": 10,
            },
            "pdf": {
                "base_kb": 30,
                "per_node_kb": 0.3,
                "max_mb": 15,
            },
            "markdown": {
                "base_kb": 1,
                "per_node_kb": 0.1,
                "max_mb": 5,
            },
            "json": {
                "base_kb": 2,
                "per_node_kb": 0.2,
                "max_mb": 10,
            },
        }

        est = estimates.get(format_type, estimates["json"])
        estimated_kb = est["base_kb"] + (node_count * est["per_node_kb"])

        return {
            "format": format_type,
            "node_count": node_count,
            "estimated_size_kb": round(estimated_kb, 1),
            "estimated_size_mb": round(estimated_kb / 1024, 2),
            "max_size_mb": est["max_mb"],
            "within_limit": (estimated_kb / 1024) < est["max_mb"],
        }
