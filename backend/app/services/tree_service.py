"""Tree node service layer for CRUD, move, and hierarchy operations."""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.tree_node import TreeNode
from app.models.activity import Activity
from app.schemas.tree_node import TreeNodeCreate, TreeNodeUpdate


class TreeService:
    """Service for tree node operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Activity-scoped queries ────────────────────────────────────────

    def get_nodes_for_activity(
        self, activity_id: int, skip: int = 0, limit: int = 100
    ) -> list[TreeNode]:
        """Return all nodes belonging to an activity."""
        self._ensure_activity_exists(activity_id)
        return (
            self.db.query(TreeNode)
            .filter(TreeNode.activity_id == activity_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_tree_for_activity(self, activity_id: int) -> list[dict]:
        """Return the full tree structure for an activity as nested dicts."""
        self._ensure_activity_exists(activity_id)
        nodes = (
            self.db.query(TreeNode)
            .filter(TreeNode.activity_id == activity_id)
            .all()
        )
        return self._build_tree(nodes)

    # ── Single-node CRUD ───────────────────────────────────────────────

    def get_node(self, node_id: int) -> TreeNode:
        """Get a single node by id or raise 404."""
        node = self.db.query(TreeNode).filter(TreeNode.id == node_id).first()
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"TreeNode {node_id} not found",
            )
        return node

    def create_node(self, data: TreeNodeCreate) -> TreeNode:
        """Create a new tree node with validation."""
        self._ensure_activity_exists(data.activity_id)

        if data.parent_id is not None:
            parent = self.get_node(data.parent_id)
            if parent.activity_id != data.activity_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent node belongs to a different activity",
                )

        self._validate_node_type(data.node_type)

        node = TreeNode(**data.model_dump())
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node

    def update_node(self, node_id: int, data: TreeNodeUpdate) -> TreeNode:
        """Update an existing node."""
        node = self.get_node(node_id)
        update_data = data.model_dump(exclude_unset=True)

        if "node_type" in update_data:
            self._validate_node_type(update_data["node_type"])

        for field, value in update_data.items():
            setattr(node, field, value)

        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node

    def delete_node(self, node_id: int) -> None:
        """Delete a node (children are cascade-deleted by the ORM)."""
        node = self.get_node(node_id)
        self.db.delete(node)
        self.db.commit()

    # ── Move / Reorder ─────────────────────────────────────────────────

    def move_node(self, node_id: int, new_parent_id: Optional[int]) -> TreeNode:
        """Move a node under a new parent (or to root if *None*).

        Guards:
        - Cannot move a node under itself.
        - Cannot create a cycle (descendant → ancestor).
        - Target parent must belong to the same activity.
        """
        node = self.get_node(node_id)

        if new_parent_id is not None:
            if new_parent_id == node_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move a node under itself",
                )

            new_parent = self.get_node(new_parent_id)
            if new_parent.activity_id != node.activity_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Target parent belongs to a different activity",
                )

            if self._is_descendant(node_id, new_parent_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move a node under one of its descendants",
                )

        node.parent_id = new_parent_id
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node

    # ── Private helpers ────────────────────────────────────────────────

    def _ensure_activity_exists(self, activity_id: int) -> None:
        activity = (
            self.db.query(Activity).filter(Activity.id == activity_id).first()
        )
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity {activity_id} not found",
            )

    @staticmethod
    def _validate_node_type(node_type: str) -> None:
        allowed = {"question", "answer", "insight"}
        if node_type not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"node_type must be one of {allowed}",
            )

    def _is_descendant(self, ancestor_id: int, candidate_id: int) -> bool:
        """Check whether *candidate_id* is a descendant of *ancestor_id*."""
        current = self.db.query(TreeNode).filter(TreeNode.id == candidate_id).first()
        while current is not None:
            if current.parent_id == ancestor_id:
                return True
            if current.parent_id is None:
                break
            current = (
                self.db.query(TreeNode)
                .filter(TreeNode.id == current.parent_id)
                .first()
            )
        return False

    @staticmethod
    def _build_tree(nodes: list[TreeNode]) -> list[dict]:
        """Build a nested dict tree from a flat list of nodes."""
        node_map: dict[int, dict] = {}
        roots: list[dict] = []

        for n in nodes:
            node_map[n.id] = {
                "id": n.id,
                "activity_id": n.activity_id,
                "parent_id": n.parent_id,
                "content": n.content,
                "node_type": n.node_type,
                "position_x": n.position_x,
                "position_y": n.position_y,
                "created_at": n.created_at.isoformat() if n.created_at else None,
                "updated_at": n.updated_at.isoformat() if n.updated_at else None,
                "children": [],
            }

        for n in nodes:
            entry = node_map[n.id]
            if n.parent_id and n.parent_id in node_map:
                node_map[n.parent_id]["children"].append(entry)
            else:
                roots.append(entry)

        return roots
