"""Follow-up question router.

Mounted at /api/questions and provides:
  POST /questions/generate         – Generate follow-up questions for a node
  POST /questions/empty-branch     – Generate questions for empty branches
  POST /questions/deep-exploration – Generate deep exploration questions
  POST /questions/connect          – Generate connection questions
"""
from fastapi import APIRouter
from app.schemas.question import (
    QuestionRequest,
    EmptyBranchRequest,
    DeepExplorationRequest,
    ConnectionRequest,
    QuestionResponse,
)
from app.services.question_service import QuestionService

router = APIRouter()

# Shared service instance (stateless, safe to reuse)
_question_service = QuestionService()


@router.post("/generate", response_model=QuestionResponse)
async def generate_questions(request: QuestionRequest) -> QuestionResponse:
    """Generate follow-up questions for a given node.

    The AI analyzes the node content, considers the age group,
    and returns contextually relevant follow-up questions.
    """
    return _question_service.generate_questions(request)


@router.post("/empty-branch", response_model=QuestionResponse)
async def generate_empty_branch_questions(request: EmptyBranchRequest) -> QuestionResponse:
    """Generate questions to stimulate ideas for empty branches.

    Helps teachers guide children to add content to branches
    that have no child nodes yet.
    """
    return _question_service.generate_for_empty_branch(request)


@router.post("/deep-exploration", response_model=QuestionResponse)
async def generate_deep_exploration_questions(request: DeepExplorationRequest) -> QuestionResponse:
    """Generate questions for deeper exploration of a topic.

    Mixes exploration and challenge questions to encourage
    children to think more critically about a topic.
    """
    return _question_service.generate_deep_exploration(request)


@router.post("/connect", response_model=QuestionResponse)
async def generate_connection_questions(request: ConnectionRequest) -> QuestionResponse:
    """Generate questions that connect two ideas.

    Helps teachers guide children to find relationships
    between different nodes in the thinking tree.
    """
    return _question_service.generate_connection_questions(request)
