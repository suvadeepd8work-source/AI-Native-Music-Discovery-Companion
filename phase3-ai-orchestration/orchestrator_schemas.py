"""
Schemas for Phase 3: AI Orchestration Layer.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PipelineStep(BaseModel):
    """Represents a step in the orchestration pipeline."""
    step_name: str = Field(..., description="Name of the pipeline step")
    step_order: int = Field(..., description="Order of execution")
    status: str = Field(..., description="Status: pending, running, completed, failed")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration_ms: Optional[float] = Field(None, description="Duration in milliseconds")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Input to the step")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Output from the step")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class OrchestrationRequest(BaseModel):
    """Request for orchestration pipeline."""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    query: str = Field(..., description="User's natural language query")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Conversation history")
    enable_recommendations: bool = Field(default=True, description="Whether to generate recommendations")
    enable_explanations: bool = Field(default=True, description="Whether to generate explanations")
    enable_review_insights: bool = Field(default=True, description="Whether to use review insights")
    max_recommendations: int = Field(default=10, ge=1, le=20, description="Maximum recommendations")


class OrchestrationResponse(BaseModel):
    """Response from orchestration pipeline."""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    query: str = Field(..., description="Original user query")
    response: str = Field(..., description="Generated conversational response")
    intent: Optional[str] = Field(None, description="Detected intent")
    parsed_query: Optional[Dict[str, Any]] = Field(None, description="Parsed query parameters")
    recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="Music recommendations")
    explanations: Optional[List[Dict[str, Any]]] = Field(None, description="Recommendation explanations")
    review_insights: Optional[Dict[str, Any]] = Field(None, description="Review insights used")
    pipeline_steps: List[PipelineStep] = Field(default_factory=list, description="Pipeline execution steps")
    total_execution_time_ms: float = Field(..., description="Total execution time")
    success: bool = Field(..., description="Whether pipeline succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")
