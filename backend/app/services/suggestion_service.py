"""Suggestion service for intelligent tree analysis and recommendations."""
from __future__ import annotations

import logging
from datetime import datetime
from difflib import SequenceMatcher
from typing import Optional
from collections import Counter

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.tree_node import TreeNode
from app.models.activity import Activity
from app.schemas.suggestion import (
    SuggestionCreate,
    SuggestionType,
    SuggestionPriority,
    SuggestionStatus,
    SuggestionResponse,
    TreeAnalysisResult,
    TreeNodeBrief,
)

logger = logging.getLogger(__name__)

# Thresholds for analysis
SIMILARITY_THRESHOLD = 0.7  # Text similarity for merge detection
MAX_BALANCED_DEPTH = 4      # Ideal max depth for children's tree
MIN_BRANCHES_FOR_BALANCE = 2  # Minimum branches for balanced tree
MAX_CHILDREN_PER_NODE = 7   # Max children before suggesting split
ORPHAN_DEPTH = 1            # Nodes at depth 1 with no children = orphan


class SuggestionService:
    """Service for generating intelligent tree suggestions."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Main Analysis ─────────────────────────────────────────────────

    def analyze_tree(self, activity_id: int) -> TreeAnalysisResult:
        """Perform full tree analysis and generate suggestions."""
        self._ensure_activity_exists(activity_id)

        nodes = (
            self.db.query(TreeNode)
            .filter(TreeNode.activity_id == activity_id)
            .all()
        )

        if not nodes:
            return TreeAnalysisResult(
                total_nodes=0,
                max_depth=0,
                balance_score=1.0,
                node_type_distribution={},
                orphan_count=0,
                deep_branch_count=0,
                suggestions=[],
            )

        # Build tree structure for analysis
        tree = self._build_tree(nodes)
        depth_map = self._calculate_depths(tree)
        max_depth = max(depth_map.values()) if depth_map else 0

        # Analyze various aspects
        suggestions: list[SuggestionResponse] = []

        # 1. Detect duplicates → merge suggestions
        merge_suggestions = self._detect_duplicates(nodes)
        suggestions.extend(merge_suggestions)

        # 2. Detect complex nodes → split suggestions
        split_suggestions = self._detect_complex_nodes(nodes)
        suggestions.extend(split_suggestions)

        # 3. Analyze balance → rebalance suggestions
        balance_suggestions = self._analyze_balance(nodes, tree, depth_map)
        suggestions.extend(balance_suggestions)

        # 4. Detect missing directions
        direction_suggestions = self._detect_missing_directions(nodes, tree)
        suggestions.extend(direction_suggestions)

        # 5. Detect related but unconnected nodes
        connect_suggestions = self._detect_unconnected_related(nodes)
        suggestions.extend(connect_suggestions)

        # Calculate metrics
        node_types = Counter(n.node_type for n in nodes)
        orphan_count = sum(1 for n in nodes if n.parent_id is None and not any(
            c.parent_id == n.id for c in nodes
        ))
        deep_branch_count = sum(1 for d in depth_map.values() if d > MAX_BALANCED_DEPTH)

        balance_score = self._calculate_balance_score(tree, depth_map)

        # Save suggestions to DB
        saved_suggestions = []
        for s in suggestions:
            db_suggestion = self._save_suggestion(activity_id, s)
            saved_suggestions.append(db_suggestion)

        return TreeAnalysisResult(
            total_nodes=len(nodes),
            max_depth=max_depth,
            balance_score=balance_score,
            node_type_distribution=dict(node_types),
            orphan_count=orphan_count,
            deep_branch_count=deep_branch_count,
            suggestions=saved_suggestions,
        )

    # ── Duplicate Detection ───────────────────────────────────────────

    def _detect_duplicates(self, nodes: list[TreeNode]) -> list[SuggestionResponse]:
        """Detect similar nodes that could be merged."""
        suggestions: list[SuggestionResponse] = []
        checked: set[tuple[int, int]] = set()

        for i, node_a in enumerate(nodes):
            for j, node_b in enumerate(nodes):
                if i >= j:
                    continue
                pair = (node_a.id, node_b.id)
                if pair in checked:
                    continue
                checked.add(pair)

                similarity = SequenceMatcher(
                    None,
                    node_a.content.lower().strip(),
                    node_b.content.lower().strip(),
                ).ratio()

                if similarity >= SIMILARITY_THRESHOLD:
                    suggestions.append(SuggestionResponse(
                        id=0,  # Will be set by DB
                        activity_id=node_a.activity_id,
                        suggestion_type=SuggestionType.MERGE,
                        priority=SuggestionPriority.HIGH if similarity > 0.85 else SuggestionPriority.MEDIUM,
                        title=f"合并相似想法",
                        description=f"「{node_a.content[:30]}...」和「{node_b.content[:30]}...」内容相似（{similarity:.0%}），建议合并。",
                        reasoning="相似的想法合并后可以减少重复，让思维树更清晰。",
                        status=SuggestionStatus.PENDING,
                        related_node_ids=[node_a.id, node_b.id],
                        suggested_content=self._merge_content(node_a.content, node_b.content),
                        suggested_parent_id=node_a.parent_id,
                        created_at=datetime.utcnow(),
                        resolved_at=None,
                    ))

        # Limit to top suggestions
        return suggestions[:5]

    # ── Complex Node Detection ────────────────────────────────────────

    def _detect_complex_nodes(self, nodes: list[TreeNode]) -> list[SuggestionResponse]:
        """Detect nodes with too many children that should be split."""
        suggestions: list[SuggestionResponse] = []

        children_count: dict[int, int] = {}
        for node in nodes:
            if node.parent_id:
                children_count[node.parent_id] = children_count.get(node.parent_id, 0) + 1

        for node_id, count in children_count.items():
            if count > MAX_CHILDREN_PER_NODE:
                parent = next((n for n in nodes if n.id == node_id), None)
                if parent:
                    children = [n for n in nodes if n.parent_id == node_id]
                    child_types = Counter(c.node_type for c in children)

                    suggestions.append(SuggestionResponse(
                        id=0,
                        activity_id=parent.activity_id,
                        suggestion_type=SuggestionType.SPLIT,
                        priority=SuggestionPriority.HIGH,
                        title=f"拆分复杂节点",
                        description=f"「{parent.content[:30]}...」有 {count} 个子节点，建议按主题分组拆分。",
                        reasoning="子节点过多会让孩子难以理解和管理。分组后更清晰。",
                        status=SuggestionStatus.PENDING,
                        related_node_ids=[node_id] + [c.id for c in children[:3]],
                        suggested_content=None,
                        suggested_parent_id=parent.parent_id,
                        created_at=datetime.utcnow(),
                        resolved_at=None,
                    ))

        return suggestions[:3]

    # ── Balance Analysis ──────────────────────────────────────────────

    def _analyze_balance(
        self,
        nodes: list[TreeNode],
        tree: list[dict],
        depth_map: dict[int, int],
    ) -> list[SuggestionResponse]:
        """Analyze tree balance and suggest rebalancing."""
        suggestions: list[SuggestionResponse] = []

        if not nodes:
            return suggestions

        # Check for deep branches
        deep_nodes = [
            nid for nid, depth in depth_map.items()
            if depth > MAX_BALANCED_DEPTH
        ]

        if deep_nodes:
            deepest_id = max(deep_nodes, key=lambda x: depth_map[x])
            deepest = next((n for n in nodes if n.id == deepest_id), None)
            if deepest:
                suggestions.append(SuggestionResponse(
                    id=0,
                    activity_id=deepest.activity_id,
                    suggestion_type=SuggestionType.REBALANCE,
                    priority=SuggestionPriority.MEDIUM,
                    title=f"树太深了",
                    description=f"分支深度达到 {depth_map[deepest_id]} 层，建议将深层节点提升或重组。",
                    reasoning="过深的树结构让孩子难以看清整体思路。适当扁平化更易理解。",
                    status=SuggestionStatus.PENDING,
                    related_node_ids=[deepest_id],
                    suggested_content=None,
                    suggested_parent_id=None,
                    created_at=datetime.utcnow(),
                    resolved_at=None,
                ))

        # Check for unbalanced branches
        root_nodes = [n for n in nodes if n.parent_id is None]
        if len(root_nodes) >= MIN_BRANCHES_FOR_BALANCE:
            branch_sizes = {}
            for root in root_nodes:
                branch_sizes[root.id] = self._count_descendants(root.id, nodes)

            max_size = max(branch_sizes.values())
            min_size = min(branch_sizes.values())

            if max_size > 0 and min_size / max_size < 0.3:
                smallest_root_id = min(branch_sizes, key=branch_sizes.get)  # type: ignore
                smallest_root = next((n for n in nodes if n.id == smallest_root_id), None)
                if smallest_root:
                    suggestions.append(SuggestionResponse(
                        id=0,
                        activity_id=smallest_root.activity_id,
                        suggestion_type=SuggestionType.NEW_DIRECTION,
                        priority=SuggestionPriority.LOW,
                        title=f"分支不均衡",
                        description=f"某些分支比其他分支丰富很多。可以给「{smallest_root.content[:20]}...」添加更多想法。",
                        reasoning="均衡的思维树能帮助孩子全面思考问题。",
                        status=SuggestionStatus.PENDING,
                        related_node_ids=[smallest_root_id],
                        suggested_content=None,
                        suggested_parent_id=None,
                        created_at=datetime.utcnow(),
                        resolved_at=None,
                    ))

        return suggestions[:2]

    # ── Missing Direction Detection ───────────────────────────────────

    def _detect_missing_directions(
        self,
        nodes: list[TreeNode],
        tree: list[dict],
    ) -> list[SuggestionResponse]:
        """Detect missing thinking directions."""
        suggestions: list[SuggestionResponse] = []

        root_nodes = [n for n in nodes if n.parent_id is None]

        # If only one root with no branches, suggest expanding
        if len(root_nodes) == 1:
            root = root_nodes[0]
            direct_children = [n for n in nodes if n.parent_id == root.id]

            if len(direct_children) < MIN_BRANCHES_FOR_BALANCE:
                suggestions.append(SuggestionResponse(
                    id=0,
                    activity_id=root.activity_id,
                    suggestion_type=SuggestionType.NEW_DIRECTION,
                    priority=SuggestionPriority.HIGH,
                    title=f"扩展思考方向",
                    description=f"「{root.content[:30]}...」目前只有 {len(direct_children)} 个分支，建议添加更多思考方向。",
                    reasoning="多角度思考能培养孩子的发散思维能力。",
                    status=SuggestionStatus.PENDING,
                    related_node_ids=[root.id],
                    suggested_content=None,
                    suggested_parent_id=root.id,
                    created_at=datetime.utcnow(),
                    resolved_at=None,
                ))

        # Check for leaf nodes that could have follow-up questions
        leaf_nodes = [
            n for n in nodes
            if not any(c.parent_id == n.id for c in nodes)
            and n.node_type == "answer"
        ]

        if len(leaf_nodes) > 2:
            # Suggest connecting some leaf answers to new questions
            sample = leaf_nodes[0]
            suggestions.append(SuggestionResponse(
                id=0,
                activity_id=sample.activity_id,
                suggestion_type=SuggestionType.CONNECT,
                priority=SuggestionPriority.LOW,
                title=f"追问深入",
                description=f"有 {len(leaf_nodes)} 个回答节点可以继续追问，引导更深入的思考。",
                reasoning="追问能帮助孩子深化理解，发现更多可能性。",
                status=SuggestionStatus.PENDING,
                related_node_ids=[n.id for n in leaf_nodes[:3]],
                suggested_content=None,
                suggested_parent_id=None,
                created_at=datetime.utcnow(),
                resolved_at=None,
            ))

        return suggestions[:2]

    # ── Unconnected Related Detection ─────────────────────────────────

    def _detect_unconnected_related(
        self,
        nodes: list[TreeNode],
    ) -> list[SuggestionResponse]:
        """Detect nodes that are related but in different branches."""
        suggestions: list[SuggestionResponse] = []
        checked: set[tuple[int, int]] = set()

        # Only check non-sibling nodes (different parents)
        for i, node_a in enumerate(nodes):
            for j, node_b in enumerate(nodes):
                if i >= j:
                    continue
                if node_a.parent_id == node_b.parent_id:
                    continue  # Skip siblings
                pair = (node_a.id, node_b.id)
                if pair in checked:
                    continue
                checked.add(pair)

                similarity = SequenceMatcher(
                    None,
                    node_a.content.lower().strip(),
                    node_b.content.lower().strip(),
                ).ratio()

                if 0.5 <= similarity < SIMILARITY_THRESHOLD:
                    suggestions.append(SuggestionResponse(
                        id=0,
                        activity_id=node_a.activity_id,
                        suggestion_type=SuggestionType.CONNECT,
                        priority=SuggestionPriority.LOW,
                        title=f"关联想法",
                        description=f"「{node_a.content[:20]}...」和「{node_b.content[:20]}...」有相似之处，可以建立关联。",
                        reasoning="发现不同分支间的联系能帮助孩子建立更完整的知识网络。",
                        status=SuggestionStatus.PENDING,
                        related_node_ids=[node_a.id, node_b.id],
                        suggested_content=None,
                        suggested_parent_id=None,
                        created_at=datetime.utcnow(),
                        resolved_at=None,
                    ))

        return suggestions[:3]

    # ── Suggestion CRUD ───────────────────────────────────────────────

    def get_suggestions(
        self,
        activity_id: int,
        status_filter: Optional[SuggestionStatus] = None,
    ) -> list[SuggestionResponse]:
        """Get suggestions for an activity."""
        from app.models.suggestion import Suggestion

        query = self.db.query(Suggestion).filter(
            Suggestion.activity_id == activity_id
        )
        if status_filter:
            query = query.filter(Suggestion.status == status_filter.value)

        return query.order_by(Suggestion.created_at.desc()).all()

    def resolve_suggestion(
        self,
        suggestion_id: int,
        action: str,
        feedback: Optional[str] = None,
    ) -> SuggestionResponse:
        """Accept, reject, or dismiss a suggestion."""
        from app.models.suggestion import Suggestion

        suggestion = self.db.query(Suggestion).filter(
            Suggestion.id == suggestion_id
        ).first()

        if not suggestion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Suggestion {suggestion_id} not found",
            )

        if action == "accept":
            suggestion.status = SuggestionStatus.ACCEPTED.value
        elif action == "reject":
            suggestion.status = SuggestionStatus.REJECTED.value
        elif action == "dismiss":
            suggestion.status = SuggestionStatus.DISMISSED.value
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action}. Must be accept, reject, or dismiss.",
            )

        suggestion.resolved_at = datetime.utcnow()
        if feedback:
            suggestion.teacher_feedback = feedback

        self.db.add(suggestion)
        self.db.commit()
        self.db.refresh(suggestion)
        return suggestion

    def get_pending_count(self, activity_id: int) -> int:
        """Get count of pending suggestions."""
        from app.models.suggestion import Suggestion

        return self.db.query(Suggestion).filter(
            Suggestion.activity_id == activity_id,
            Suggestion.status == SuggestionStatus.PENDING.value,
        ).count()

    # ── Private Helpers ───────────────────────────────────────────────

    def _save_suggestion(self, activity_id: int, suggestion: SuggestionResponse) -> SuggestionResponse:
        """Save a suggestion to the database."""
        from app.models.suggestion import Suggestion

        db_suggestion = Suggestion(
            activity_id=activity_id,
            suggestion_type=suggestion.suggestion_type.value,
            priority=suggestion.priority.value,
            title=suggestion.title,
            description=suggestion.description,
            reasoning=suggestion.reasoning,
            status=SuggestionStatus.PENDING.value,
            related_node_ids=",".join(str(i) for i in suggestion.related_node_ids),
            suggested_content=suggestion.suggested_content,
            suggested_parent_id=suggestion.suggested_parent_id,
        )
        self.db.add(db_suggestion)
        self.db.commit()
        self.db.refresh(db_suggestion)

        # Update response with DB id
        suggestion.id = db_suggestion.id
        return suggestion

    def _ensure_activity_exists(self, activity_id: int) -> None:
        """Ensure activity exists."""
        activity = (
            self.db.query(Activity).filter(Activity.id == activity_id).first()
        )
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity {activity_id} not found",
            )

    @staticmethod
    def _build_tree(nodes: list[TreeNode]) -> list[dict]:
        """Build nested tree structure from flat node list."""
        node_map: dict[int, dict] = {}
        roots: list[dict] = []

        for n in nodes:
            node_map[n.id] = {
                "id": n.id,
                "parent_id": n.parent_id,
                "content": n.content,
                "node_type": n.node_type,
                "children": [],
            }

        for n in nodes:
            entry = node_map[n.id]
            if n.parent_id and n.parent_id in node_map:
                node_map[n.parent_id]["children"].append(entry)
            else:
                roots.append(entry)

        return roots

    @staticmethod
    def _calculate_depths(tree: list[dict], current_depth: int = 0) -> dict[int, int]:
        """Calculate depth of each node."""
        depths: dict[int, int] = {}
        for node in tree:
            depths[node["id"]] = current_depth
            child_depths = SuggestionService._calculate_depths(
                node["children"], current_depth + 1
            )
            depths.update(child_depths)
        return depths

    @staticmethod
    def _calculate_balance_score(tree: list[dict], depth_map: dict[int, int]) -> float:
        """Calculate tree balance score (0-1)."""
        if not depth_map:
            return 1.0

        max_depth = max(depth_map.values())
        if max_depth == 0:
            return 1.0

        # Penalize deep trees and unbalanced branches
        depth_penalty = min(max_depth / (MAX_BALANCED_DEPTH * 2), 0.5)

        # Calculate branch variance
        root_children = len(tree)
        if root_children < MIN_BRANCHES_FOR_BALANCE:
            branch_penalty = 0.3
        else:
            branch_penalty = 0.0

        score = 1.0 - depth_penalty - branch_penalty
        return max(0.0, min(1.0, score))

    @staticmethod
    def _count_descendants(node_id: int, nodes: list[TreeNode]) -> int:
        """Count all descendants of a node."""
        children = [n for n in nodes if n.parent_id == node_id]
        return len(children) + sum(
            SuggestionService._count_descendants(c.id, nodes) for c in children
        )

    @staticmethod
    def _merge_content(content_a: str, content_b: str) -> str:
        """Merge two similar contents into one."""
        # Simple merge: use the longer one with a note
        if len(content_a) >= len(content_b):
            return f"{content_a}（合并自相似想法）"
        return f"{content_b}（合并自相似想法）"
