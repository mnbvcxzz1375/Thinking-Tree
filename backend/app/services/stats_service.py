"""Statistics service for activity review and analytics."""
from __future__ import annotations

from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.speech_record import SpeechRecord
from app.models.teacher_review import TeacherReview
from app.models.tree_node import TreeNode
from app.schemas.stats import (
    ActivityInsights,
    ActivityStats,
    BranchStats,
    InsightItem,
    NodeCountByType,
    OverviewStats,
    TimeDistribution,
)


class StatsService:
    """Service for computing activity statistics."""

    def __init__(self, db: Session) -> None:
        self.db: Session = db

    # ── Public API ──────────────────────────────────────────────────────

    def get_activity_stats(self, activity_id: int) -> ActivityStats:
        """Compute comprehensive statistics for a single activity."""
        activity = self._get_activity(activity_id)
        nodes = self._get_nodes(activity_id)
        speech_count = self._count_speech_records(activity_id)
        review_stats = self._get_review_stats(activity_id)

        node_counts = self._count_nodes_by_type(nodes)
        depths = self._compute_depths(nodes)
        max_depth = max(depths.values()) if depths else 0
        avg_depth = sum(depths.values()) / len(depths) if depths else 0.0
        time_dist = self._compute_time_distribution(nodes)
        branches = self._find_most_active_branches(nodes, top_n=5)
        participation = self._compute_participation_rate(nodes, speech_count)

        last_node = max(
            (n.created_at for n in nodes if n.created_at is not None),
            default=None,
        )

        return ActivityStats(
            activity_id=int(activity.id),
            activity_title=str(activity.title),
            node_counts=node_counts,
            max_depth=max_depth,
            avg_depth=round(avg_depth, 2),
            total_speech_records=speech_count,
            total_reviews=review_stats["total"],
            approved_reviews=review_stats["approved"],
            participation_rate=round(participation, 2),
            most_active_branches=branches,
            time_distribution=time_dist,
            created_at=activity.created_at,
            last_node_at=last_node,
        )

    def get_activity_insights(self, activity_id: int) -> ActivityInsights:
        """Generate insights for an activity."""
        stats = self.get_activity_stats(activity_id)
        insights: list[InsightItem] = []

        # Depth insight
        if stats.max_depth >= 5:
            insights.append(
                InsightItem(
                    category="depth",
                    title="思维深度优秀",
                    description=f"思维树最大深度达到 {stats.max_depth} 层，展现了深入的思考能力。",
                    severity="success",
                )
            )
        elif stats.max_depth >= 3:
            insights.append(
                InsightItem(
                    category="depth",
                    title="思维深度良好",
                    description=f"思维树最大深度为 {stats.max_depth} 层，鼓励继续深入探索。",
                    severity="info",
                )
            )
        else:
            insights.append(
                InsightItem(
                    category="depth",
                    title="需要更多深入思考",
                    description=f"思维树深度仅 {stats.max_depth} 层，建议引导孩子提出更多追问。",
                    severity="warning",
                )
            )

        # Participation insight
        if stats.participation_rate >= 0.7:
            insights.append(
                InsightItem(
                    category="participation",
                    title="参与度高",
                    description=f"语音互动参与率 {stats.participation_rate * 100:.0f}%，孩子积极参与思考。",
                    severity="success",
                )
            )
        elif stats.participation_rate >= 0.3:
            insights.append(
                InsightItem(
                    category="participation",
                    title="参与度中等",
                    description=f"语音互动参与率 {stats.participation_rate * 100:.0f}%，可进一步鼓励表达。",
                    severity="info",
                )
            )
        else:
            insights.append(
                InsightItem(
                    category="participation",
                    title="参与度偏低",
                    description=f"语音互动参与率仅 {stats.participation_rate * 100:.0f}%，需要更多引导和鼓励。",
                    severity="warning",
                )
            )

        # Growth insight
        if len(stats.time_distribution) >= 3:
            recent = stats.time_distribution[-3:]
            trend = sum(t.count for t in recent) / 3
            if trend > 5:
                insights.append(
                    InsightItem(
                        category="growth",
                        title="活跃度上升",
                        description="最近几天节点创建频率明显提升，思维活跃度增强。",
                        severity="success",
                    )
                )

        # Balance insight
        nc = stats.node_counts
        if nc.total > 0:
            q_ratio = nc.question / nc.total
            a_ratio = nc.answer / nc.total
            if q_ratio > 0.5:
                insights.append(
                    InsightItem(
                        category="balance",
                        title="问题导向型思维",
                        description="问题节点占比超过一半，体现了强烈的好奇心。",
                        severity="info",
                    )
                )
            elif a_ratio > 0.5:
                insights.append(
                    InsightItem(
                        category="balance",
                        title="回答导向型思维",
                        description="回答节点占比超过一半，展现了良好的回答能力。",
                        severity="info",
                    )
                )

        # Teacher review insight
        if stats.total_reviews > 0:
            approval_rate = stats.approved_reviews / stats.total_reviews
            if approval_rate >= 0.8:
                insights.append(
                    InsightItem(
                        category="review",
                        title="教师评价积极",
                        description=f"教师审核通过率 {approval_rate * 100:.0f}%，整体质量优秀。",
                        severity="success",
                    )
                )

        summary = self._generate_summary(stats, insights)

        return ActivityInsights(
            activity_id=activity_id,
            insights=insights,
            summary=summary,
        )

    def get_overview_stats(self) -> OverviewStats:
        """Compute overview statistics across all activities."""
        total_activities: int = self.db.query(Activity).count()
        active_activities: int = self.db.query(Activity).filter(Activity.is_active == True).count()
        total_nodes: int = self.db.query(TreeNode).count()
        total_speech: int = self.db.query(SpeechRecord).count()
        total_reviews: int = self.db.query(TeacherReview).count()

        avg_nodes = total_nodes / total_activities if total_activities > 0 else 0.0

        # Get recent activity stats
        recent_activities_db = (
            self.db.query(Activity)
            .order_by(Activity.created_at.desc())
            .limit(5)
            .all()
        )
        recent_stats: list[ActivityStats] = [
            self.get_activity_stats(int(a.id)) for a in recent_activities_db
        ]

        return OverviewStats(
            total_activities=total_activities,
            active_activities=active_activities,
            total_nodes=total_nodes,
            total_speech_records=total_speech,
            total_reviews=total_reviews,
            avg_nodes_per_activity=round(avg_nodes, 1),
            recent_activities=recent_stats,
        )

    # ── Private helpers ─────────────────────────────────────────────────

    def _get_activity(self, activity_id: int) -> Activity:
        """Get activity or raise."""
        activity = self.db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise ValueError(f"Activity {activity_id} not found")
        return activity

    def _get_nodes(self, activity_id: int) -> list[TreeNode]:
        """Get all nodes for an activity."""
        return (
            self.db.query(TreeNode)
            .filter(TreeNode.activity_id == activity_id)
            .all()
        )

    def _count_speech_records(self, activity_id: int) -> int:
        """Count speech records for an activity."""
        return (
            self.db.query(SpeechRecord)
            .filter(SpeechRecord.activity_id == activity_id)
            .count()
        )

    def _get_review_stats(self, activity_id: int) -> dict[str, int]:
        """Get review statistics for an activity."""
        reviews = (
            self.db.query(TeacherReview)
            .join(TreeNode, TeacherReview.tree_node_id == TreeNode.id)
            .filter(TreeNode.activity_id == activity_id)
            .all()
        )
        total: int = len(reviews)
        approved: int = sum(1 for r in reviews if int(r.is_approved) == 1)
        return {"total": total, "approved": approved}

    @staticmethod
    def _count_nodes_by_type(nodes: list[TreeNode]) -> NodeCountByType:
        """Count nodes grouped by type."""
        counts: dict[str, int] = defaultdict(int)
        for node in nodes:
            node_type: str = str(node.node_type)
            counts[node_type] += 1
        total = sum(counts.values())
        return NodeCountByType(
            question=counts.get("question", 0),
            answer=counts.get("answer", 0),
            insight=counts.get("insight", 0),
            root=counts.get("root", 0),
            branch=counts.get("branch", 0),
            total=total,
        )

    @staticmethod
    def _compute_depths(nodes: list[TreeNode]) -> dict[int, int]:
        """Compute depth for each node (distance from root)."""
        node_map: dict[int, TreeNode] = {}
        for n in nodes:
            node_map[int(n.id)] = n
        depths: dict[int, int] = {}

        def _depth(node_id: int) -> int:
            if node_id in depths:
                return depths[node_id]
            node = node_map.get(node_id)
            if node is None or node.parent_id is None:
                depths[node_id] = 0
                return 0
            d = _depth(int(node.parent_id)) + 1
            depths[node_id] = d
            return d

        for node in nodes:
            _depth(int(node.id))

        return depths

    @staticmethod
    def _compute_time_distribution(nodes: list[TreeNode]) -> list[TimeDistribution]:
        """Compute node creation time distribution by date."""
        date_counts: dict[str, int] = defaultdict(int)
        for node in nodes:
            created_at = node.created_at
            if created_at is not None:
                date_str = created_at.strftime("%Y-%m-%d")
                date_counts[date_str] += 1

        return [
            TimeDistribution(date=date, count=count)
            for date, count in sorted(date_counts.items())
        ]

    @staticmethod
    def _find_most_active_branches(
        nodes: list[TreeNode], top_n: int = 5
    ) -> list[BranchStats]:
        """Find the most active branches (root-level children by node count)."""
        children_map: dict[int | None, list[TreeNode]] = defaultdict(list)
        for node in nodes:
            parent_id = int(node.parent_id) if node.parent_id is not None else None
            children_map[parent_id].append(node)

        def _count_descendants(node_id: int) -> tuple[int, int]:
            """Return (count, max_depth) for subtree."""
            kids = children_map.get(node_id, [])
            if not kids:
                return 1, 0
            total = 1
            max_d = 0
            for kid in kids:
                c, d = _count_descendants(int(kid.id))
                total += c
                max_d = max(max_d, d + 1)
            return total, max_d

        # Find root nodes (parent_id is None)
        roots = children_map.get(None, [])
        branches: list[BranchStats] = []
        for root in roots:
            count, depth = _count_descendants(int(root.id))
            root_content: str = str(root.content)
            last = root.created_at
            branches.append(
                BranchStats(
                    node_id=int(root.id),
                    content=root_content[:50] + ("..." if len(root_content) > 50 else ""),
                    depth=depth,
                    node_count=count,
                    last_activity=last.isoformat() if last is not None else None,
                )
            )

        branches.sort(key=lambda b: b.node_count, reverse=True)
        return branches[:top_n]

    @staticmethod
    def _compute_participation_rate(
        nodes: list[TreeNode], speech_count: int
    ) -> float:
        """Compute participation rate as speech_count / node_count (capped at 1.0)."""
        if not nodes:
            return 0.0
        return min(speech_count / len(nodes), 1.0)

    @staticmethod
    def _generate_summary(
        stats: ActivityStats, insights: list[InsightItem]
    ) -> str:
        """Generate a text summary from stats and insights."""
        parts: list[str] = []
        parts.append(f"活动「{stats.activity_title}」共创建 {stats.node_counts.total} 个思维节点。")
        parts.append(f"树最大深度 {stats.max_depth} 层，平均深度 {stats.avg_depth} 层。")

        if stats.total_speech_records > 0:
            parts.append(f"语音互动 {stats.total_speech_records} 次。")
        if stats.total_reviews > 0:
            parts.append(f"教师评价 {stats.total_reviews} 条，其中 {stats.approved_reviews} 条通过。")

        warnings = [i for i in insights if i.severity == "warning"]
        if warnings:
            parts.append(f"有 {len(warnings)} 项需要关注。")

        return " ".join(parts)
