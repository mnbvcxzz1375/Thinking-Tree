"""Follow-up question generation service with mock AI.

This service generates age-appropriate follow-up questions for teachers
to ask children during thinking tree activities. Uses mock generation
until real AI integration is added.
"""
from __future__ import annotations

import random
import uuid
import logging

from app.schemas.question import (
    FollowUpQuestion,
    QuestionRequest,
    EmptyBranchRequest,
    DeepExplorationRequest,
    ConnectionRequest,
    QuestionResponse,
)

logger = logging.getLogger(__name__)


# ── Question templates by category and age group ────────────────────────

_TEMPLATES: dict[str, dict[str, list[str]]] = {
    "exploration": {
        "4-6": [
            "你能告诉我更多关于{topic}的事情吗？",
            "{topic}是什么样子的呀？",
            "你觉得{topic}好不好玩？为什么呢？",
            "你是怎么知道{topic}的？",
            "{topic}让你想到了什么？",
        ],
        "7-9": [
            "你能详细说说{topic}是怎么回事吗？",
            "你觉得{topic}最重要的部分是什么？",
            "{topic}和你之前想的有什么不一样吗？",
            "如果要给别人介绍{topic}，你会怎么说？",
            "关于{topic}，你还想知道什么？",
        ],
        "10-12": [
            "你认为{topic}背后的原因是什么？",
            "关于{topic}，有哪些是你已经确定的，哪些还不太确定？",
            "如果要深入研究{topic}，你会从哪里开始？",
            "{topic}有哪些方面是你还没有考虑到的？",
            "你能用不同的方式来解释{topic}吗？",
        ],
    },
    "connection": {
        "4-6": [
            "{source}和{target}有什么一样的地方吗？",
            "{source}和{target}是好朋友吗？",
            "你觉得{source}喜欢{target}吗？为什么？",
            "{source}和{target}放在一起会怎么样呢？",
        ],
        "7-9": [
            "{source}和{target}之间有什么联系呢？",
            "你觉得{source}和{target}有什么相同和不同？",
            "如果把{source}和{target}放在一起想，你会得出什么新想法？",
            "{source}是怎么影响{target}的？",
        ],
        "10-12": [
            "从{source}的角度来看{target}，你有什么新的理解？",
            "{source}和{target}之间的关系说明了什么更深层的道理？",
            "你能找到{source}和{target}之间更本质的联系吗？",
            "如果{source}不存在，{target}会有什么不同？",
        ],
    },
    "reflection": {
        "4-6": [
            "你觉得自己做得怎么样呀？",
            "这个{topic}让你开心吗？",
            "如果再来一次，你会怎么做呢？",
            "你最喜欢{topic}的哪个部分？",
        ],
        "7-9": [
            "回顾一下关于{topic}的讨论，你有什么新的想法？",
            "你觉得自己的想法有没有发生变化？",
            "关于{topic}，你最自豪的发现是什么？",
            "如果时间更多，你还想探索{topic}的哪些方面？",
        ],
        "10-12": [
            "通过探索{topic}，你对自己有了什么新的认识？",
            "你的思考过程是怎样的？你是怎么得出这个结论的？",
            "关于{topic}，你的观点是如何演变的？",
            "这次探索{topic}的经历，对你以后思考问题有什么帮助？",
        ],
    },
    "challenge": {
        "4-6": [
            "如果不是这样呢？会怎么样呀？",
            "有人可能觉得不一样哦，你怎么看？",
            "你确定吗？我们再想想看？",
            "如果反过来想呢？",
        ],
        "7-9": [
            "有没有可能你的想法不完全对呢？",
            "换个角度想，会不会有不一样的结论？",
            "你能想到反对你观点的理由吗？",
            "如果有人不同意你的看法，你会怎么说服他们？",
        ],
        "10-12": [
            "你的论据足够支持你的结论吗？",
            "有没有什么前提假设是你没有检验过的？",
            "如果考虑相反的证据，你的结论还成立吗？",
            "你能区分事实和观点吗？关于{topic}，哪些是事实？",
        ],
    },
    "creative": {
        "4-6": [
            "如果你是{topic}，你会做什么呢？",
            "你能给{topic}画一幅画吗？画里有什么？",
            "如果{topic}会说话，它会说什么？",
            "你能编一个关于{topic}的小故事吗？",
        ],
        "7-9": [
            "如果{topic}存在于另一个世界，那会是什么样的？",
            "你能发明一个和{topic}有关的新东西吗？",
            "如果让你来重新设计{topic}，你会怎么做？",
            "用一个比喻来形容{topic}，你会怎么说？",
        ],
        "10-12": [
            "如果{topic}在未来100年后会怎样？",
            "你能用一种全新的方式来理解{topic}吗？",
            "如果把{topic}和一个完全不同的领域结合，会产生什么？",
            "关于{topic}，什么样的实验或探索能帮助你验证想法？",
        ],
    },
    "empty_branch": {
        "4-6": [
            "关于{parent}，你能想到什么呢？",
            "{parent}里面藏着什么秘密呀？",
            "我们来给{parent}找一些小伙伴吧！",
            "你觉得{parent}还能变成什么？",
        ],
        "7-9": [
            "关于{parent}，你还有什么想法没有说出来？",
            "我们可以在{parent}下面添加什么新内容？",
            "{parent}可以分成几个小部分来思考？",
            "如果要更详细地了解{parent}，我们需要什么信息？",
        ],
        "10-12": [
            "关于{parent}，有哪些子主题值得深入探索？",
            "如果把{parent}分解成更小的问题，会是哪些？",
            "关于{parent}，你有哪些假设需要验证？",
            "要全面理解{parent}，我们需要从哪些角度来分析？",
        ],
    },
}

# ── Category context messages ────────────────────────────────────────────

_CATEGORY_CONTEXT: dict[str, dict[str, str]] = {
    "exploration": {
        "4-6": "帮助孩子更深入地了解这个话题",
        "7-9": "鼓励孩子更详细地探索和描述",
        "10-12": "引导孩子进行更深入的分析和研究",
    },
    "connection": {
        "4-6": "帮助孩子发现事物之间的联系",
        "7-9": "引导孩子思考不同想法之间的关系",
        "10-12": "培养孩子的系统思维和关联分析能力",
    },
    "reflection": {
        "4-6": "让孩子回顾和感受自己的想法",
        "7-9": "帮助孩子反思自己的思考过程",
        "10-12": "培养孩子的元认知能力",
    },
    "challenge": {
        "4-6": "用温和的方式鼓励孩子换个角度想",
        "7-9": "培养孩子的批判性思维",
        "10-12": "训练孩子的逻辑推理和论证能力",
    },
    "creative": {
        "4-6": "用想象力和游戏来探索想法",
        "7-9": "鼓励创新思维和创造性表达",
        "10-12": "培养创造性问题解决能力",
    },
    "empty_branch": {
        "4-6": "启发孩子在这个方向上展开想象",
        "7-9": "引导孩子在这个主题下产生新想法",
        "10-12": "帮助孩子识别这个主题下的待探索领域",
    },
}


def _generate_id() -> str:
    """Generate a unique question ID."""
    return f"q_{uuid.uuid4().hex[:12]}"


def _extract_topic(content: str, max_len: int = 20) -> str:
    """Extract a short topic phrase from node content."""
    # Simple heuristic: take first N chars or up to first punctuation
    clean = content.strip()
    for sep in ["。", "！", "？", "，", ".", "!", "?", ","]:
        idx = clean.find(sep)
        if 0 < idx < max_len:
            return clean[:idx]
    if len(clean) <= max_len:
        return clean
    return clean[:max_len] + "..."


def _select_templates(
    category: str,
    age_group: str,
    count: int,
) -> list[str]:
    """Select random templates for a category and age group."""
    cat_templates = _TEMPLATES.get(category, {})
    templates = cat_templates.get(age_group, cat_templates.get("7-9", []))
    if not templates:
        return []
    # Sample without replacement if enough, otherwise allow repeats
    if count <= len(templates):
        return random.sample(templates, count)
    return random.choices(templates, k=count)


def _fill_template(
    template: str,
    topic: str = "",
    source: str = "",
    target: str = "",
    parent: str = "",
) -> str:
    """Fill template placeholders with provided values."""
    return (
        template.replace("{topic}", topic)
        .replace("{source}", source)
        .replace("{target}", target)
        .replace("{parent}", parent)
    )


class QuestionService:
    """Service for generating follow-up questions (mock implementation)."""

    def generate_questions(self, request: QuestionRequest) -> QuestionResponse:
        """Generate follow-up questions for a node.

        Uses mock templates. In production, this would call an LLM.
        """
        topic = _extract_topic(request.node_content)
        age = request.age_group
        categories = (
            [request.category]
            if request.category
            else ["exploration", "reflection", "challenge", "creative"]
        )

        questions: list[FollowUpQuestion] = []
        per_category = max(1, request.count // len(categories))
        remaining = request.count

        for cat in categories:
            n = per_category if cat != categories[-1] else remaining
            templates = _select_templates(cat, age, n)
            for tpl in templates:
                filled = _fill_template(tpl, topic=topic)
                variations = self._generate_variations(filled, cat, age, topic)
                context = _CATEGORY_CONTEXT.get(cat, {}).get(
                    age, _CATEGORY_CONTEXT.get(cat, {}).get("7-9", "")
                )
                questions.append(
                    FollowUpQuestion(
                        id=_generate_id(),
                        question=filled,
                        category=cat,
                        age_group=age,
                        relevance_score=round(random.uniform(0.6, 1.0), 2),
                        context=context,
                        variations=variations,
                    )
                )
            remaining -= len(templates)

        return QuestionResponse(
            questions=questions[: request.count],
            source_node_content=request.node_content,
            age_group=age,
            category=request.category,
        )

    def generate_for_empty_branch(self, request: EmptyBranchRequest) -> QuestionResponse:
        """Generate questions to stimulate ideas for empty branches."""
        parent_topic = _extract_topic(request.parent_content)
        age = request.age_group

        templates = _select_templates("empty_branch", age, request.count)
        questions: list[FollowUpQuestion] = []

        for tpl in templates:
            filled = _fill_template(tpl, parent=parent_topic)
            variations = self._generate_variations(filled, "empty_branch", age, parent_topic)
            context = _CATEGORY_CONTEXT["empty_branch"].get(
                age, _CATEGORY_CONTEXT["empty_branch"]["7-9"]
            )
            questions.append(
                FollowUpQuestion(
                    id=_generate_id(),
                    question=filled,
                    category="empty_branch",
                    age_group=age,
                    relevance_score=round(random.uniform(0.7, 1.0), 2),
                    context=context,
                    variations=variations,
                )
            )

        return QuestionResponse(
            questions=questions,
            source_node_content=request.parent_content,
            age_group=age,
            category="empty_branch",
        )

    def generate_deep_exploration(self, request: DeepExplorationRequest) -> QuestionResponse:
        """Generate questions for deeper exploration of a topic."""
        topic = _extract_topic(request.node_content)
        age = request.age_group

        # Mix exploration with challenge for deeper thinking
        categories = ["exploration", "challenge"]
        questions: list[FollowUpQuestion] = []
        per_cat = max(1, request.count // 2)
        remaining = request.count

        for cat in categories:
            n = per_cat if cat != categories[-1] else remaining
            templates = _select_templates(cat, age, n)
            for tpl in templates:
                filled = _fill_template(tpl, topic=topic)
                variations = self._generate_variations(filled, cat, age, topic)
                context = _CATEGORY_CONTEXT.get(cat, {}).get(
                    age, _CATEGORY_CONTEXT.get(cat, {}).get("7-9", "")
                )
                # Boost relevance for deep exploration
                score = round(random.uniform(0.75, 1.0), 2)
                questions.append(
                    FollowUpQuestion(
                        id=_generate_id(),
                        question=filled,
                        category=cat,
                        age_group=age,
                        relevance_score=score,
                        context=f"深度探索 · {context}",
                        variations=variations,
                    )
                )
            remaining -= len(templates)

        return QuestionResponse(
            questions=questions[: request.count],
            source_node_content=request.node_content,
            age_group=age,
            category="exploration+challenge",
        )

    def generate_connection_questions(self, request: ConnectionRequest) -> QuestionResponse:
        """Generate questions that connect two ideas."""
        source_topic = _extract_topic(request.source_content)
        target_topic = _extract_topic(request.target_content)
        age = request.age_group

        templates = _select_templates("connection", age, request.count)
        questions: list[FollowUpQuestion] = []

        for tpl in templates:
            filled = _fill_template(tpl, source=source_topic, target=target_topic)
            variations = self._generate_variations(filled, "connection", age, source_topic)
            context = _CATEGORY_CONTEXT["connection"].get(
                age, _CATEGORY_CONTEXT["connection"]["7-9"]
            )
            questions.append(
                FollowUpQuestion(
                    id=_generate_id(),
                    question=filled,
                    category="connection",
                    age_group=age,
                    relevance_score=round(random.uniform(0.65, 1.0), 2),
                    context=context,
                    variations=variations,
                )
            )

        return QuestionResponse(
            questions=questions,
            source_node_content=request.source_content,
            age_group=age,
            category="connection",
        )

    def _generate_variations(
        self, original: str, category: str, age: str, topic: str
    ) -> list[str]:
        """Generate alternative phrasings for a question."""
        # Simple mock: pick 1-2 other templates from same category
        templates = _TEMPLATES.get(category, {}).get(age, [])
        candidates = [t for t in templates if _fill_template(t, topic=topic, parent=topic) != original]
        if not candidates:
            return []
        chosen = random.sample(candidates, min(2, len(candidates)))
        return [_fill_template(t, topic=topic, parent=topic) for t in chosen]
