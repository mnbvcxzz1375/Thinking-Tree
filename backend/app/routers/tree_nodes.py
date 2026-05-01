"""Standalone tree-nodes router.

Mounted at /api/nodes and provides:
  GET    /nodes/{node_id}      – get node details
  PUT    /nodes/{node_id}      – update node
  DELETE /nodes/{node_id}      – delete node
  POST   /nodes/{node_id}/move – move node to new parent
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.tree_node import TreeNode
from app.schemas.tree_node import (
    TreeNodeCreate,
    TreeNodeMove,
    TreeNodeResponse,
    TreeNodeUpdate,
)
from app.services.tree_service import TreeService

router = APIRouter()


@router.get("", response_model=List[TreeNodeResponse])
async def list_tree_nodes(
    activity_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[TreeNode]:
    """List tree nodes, optionally filtered by activity (legacy endpoint)."""
    query = db.query(TreeNode)
    if activity_id:
        query = query.filter(TreeNode.activity_id == activity_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=TreeNodeResponse, status_code=status.HTTP_201_CREATED)
async def create_tree_node(
    node: TreeNodeCreate,
    db: Session = Depends(get_db),
) -> TreeNode:
    """Create a new tree node (legacy endpoint)."""
    svc = TreeService(db)
    return svc.create_node(node)


@router.get("/{node_id}", response_model=TreeNodeResponse)
async def get_tree_node(
    node_id: int,
    db: Session = Depends(get_db),
) -> TreeNode:
    """Get tree node by ID."""
    svc = TreeService(db)
    return svc.get_node(node_id)


@router.put("/{node_id}", response_model=TreeNodeResponse)
async def update_tree_node(
    node_id: int,
    node: TreeNodeUpdate,
    db: Session = Depends(get_db),
) -> TreeNode:
    """Update a tree node."""
    svc = TreeService(db)
    return svc.update_node(node_id, node)


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tree_node(
    node_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete a tree node."""
    svc = TreeService(db)
    svc.delete_node(node_id)


@router.post("/{node_id}/move", response_model=TreeNodeResponse)
async def move_tree_node(
    node_id: int,
    body: TreeNodeMove,
    db: Session = Depends(get_db),
) -> TreeNode:
    """Move a tree node to a new parent (or to root if new_parent_id is null)."""
    svc = TreeService(db)
    return svc.move_node(node_id, body.new_parent_id)
