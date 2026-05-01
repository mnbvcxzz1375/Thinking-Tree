"""Activity-nodes sub-router.

Mounted under /api/activities and provides:
  GET  /{activity_id}/nodes       – list nodes for an activity
  GET  /{activity_id}/nodes/tree  – full nested tree
  POST /{activity_id}/nodes       – create a node within an activity
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.tree_node import TreeNode
from app.schemas.tree_node import (
    TreeNodeCreate,
    TreeNodeCreateInActivity,
    TreeNodeResponse,
    TreeNodeTreeResponse,
)
from app.services.tree_service import TreeService

router = APIRouter()


@router.get("/{activity_id}/nodes", response_model=List[TreeNodeResponse])
async def list_activity_nodes(
    activity_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[TreeNode]:
    """List all tree nodes belonging to an activity."""
    svc = TreeService(db)
    return svc.get_nodes_for_activity(activity_id, skip=skip, limit=limit)


@router.get("/{activity_id}/nodes/tree", response_model=List[TreeNodeTreeResponse])
async def get_activity_tree(
    activity_id: int,
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return the full nested tree structure for an activity."""
    svc = TreeService(db)
    return svc.get_tree_for_activity(activity_id)


@router.post(
    "/{activity_id}/nodes",
    response_model=TreeNodeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_activity_node(
    activity_id: int,
    node: TreeNodeCreateInActivity,
    db: Session = Depends(get_db),
) -> TreeNode:
    """Create a new tree node within an activity."""
    svc = TreeService(db)
    full_data = TreeNodeCreate(
        activity_id=activity_id,
        parent_id=node.parent_id,
        content=node.content,
        node_type=node.node_type,
        position_x=node.position_x,
        position_y=node.position_y,
    )
    return svc.create_node(full_data)
