"""
Orchestrator for Phase 3: AI Orchestration Layer.
Executes the complete pipeline from conversation to response.
"""
import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

from .orchestrator_schemas import OrchestrationRequest, OrchestrationResponse, PipelineStep
from .orchestration_logger import OrchestrationLogger, MockOrchestrationLogger


logger = structlog.get_logger(__name__)


class Orchestrator:
    """
    Orchestrates the complete AI music discovery pipeline.
    
    Pipeline:
    1. Conversation Engine (Intent Recognition, Query Parsing)
    2. Conversation Memory (Retrieve context)
    3. Review Insight Retrieval (Fetch insights from Phase 2)
    4. Prompt Builder (Build optimized prompt)
    5. Groq (Generate response via Response Generator)
    6. Music Recommendation Engine (Generate recommendations)
    7. Explainability Engine (Generate explanations)
    8. Response Generator (Final conversational response)
    """
    
    def __init__(
        self,
        conversation_engine: Any,  # Phase 1 components
        conversation_memory: Any,
        review_client: Any,  # Phase 2 components
        recommendation_engine: Any,
        explainability_engine: Any,
        response_generator: Any,  # Phase 1 component
        orchestration_logger: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.conversation_engine = conversation_engine
        self.conversation_memory = conversation_memory
        self.review_client = review_client
        self.recommendation_engine = recommendation_engine
        self.explainability_engine = explainability_engine
        self.response_generator = response_generator
        self.orchestration_logger = orchestration_logger or OrchestrationLogger(config.get("orchestration_logger", {}) if config else {})
        self.config = config or {}
        
        self.pipeline_steps = [
            "conversation_engine",
            "conversation_memory",
            "review_insight_retrieval",
            "prompt_building",
            "recommendation_generation",
            "explanation_generation",
            "response generation"
        ]
    
    async def orchestrate(self, request: OrchestrationRequest) -> OrchestrationResponse:
        """
        Execute the complete orchestration pipeline.
        
        Args:
            request: Orchestration request with user query and context
            
        Returns:
            OrchestrationResponse with results and pipeline execution details
        """
        start_time = time.time()
        pipeline_steps: List[PipelineStep] = []
        
        # Generate pipeline ID
        pipeline_id = f"pipeline_{request.user_id}_{request.session_id}_{int(start_time * 1000)}"
        
        # Log execution start
        execution_id = self.orchestration_logger.log_execution_start(
            user_id=request.user_id,
            session_id=request.session_id,
            query=request.query,
            pipeline_id=pipeline_id
        )
        
        try:
            logger.info(
                "Starting orchestration pipeline",
                user_id=request.user_id,
                session_id=request.session_id,
                query=request.query,
                execution_id=execution_id
            )
            
            # Step 1: Conversation Engine (Intent Recognition + Query Parsing)
            self.orchestration_logger.log_module_start(execution_id, "conversation_engine", 1)
            step = await self._execute_conversation_engine(request, pipeline_steps, execution_id)
            self.orchestration_logger.log_module_complete(
                execution_id, "conversation_engine", step.success,
                step.output_data, step.error_message
            )
            if not step.success:
                self.orchestration_logger.log_failure(
                    execution_id, "conversation_engine", "StepFailure",
                    step.error_message or "Unknown error"
                )
                return self._build_error_response(request, pipeline_steps, start_time, step.error_message, execution_id)
            
            intent = step.output_data.get("intent")
            parsed_query = step.output_data.get("parsed_query")
            
            # Step 2: Conversation Memory (Retrieve context)
            self.orchestration_logger.log_module_start(execution_id, "conversation_memory", 2)
            step = await self._execute_conversation_memory(request, pipeline_steps, execution_id)
            self.orchestration_logger.log_module_complete(
                execution_id, "conversation_memory", step.success,
                step.output_data, step.error_message
            )
            memory = step.output_data.get("memory", {})
            
            # Step 3: Review Insight Retrieval
            review_insights = None
            if request.enable_review_insights:
                self.orchestration_logger.log_module_start(execution_id, "review_insight_retrieval", 3)
                step = await self._execute_review_insight_retrieval(request, pipeline_steps, execution_id)
                self.orchestration_logger.log_module_complete(
                    execution_id, "review_insight_retrieval", step.success,
                    step.output_data, step.error_message
                )
                if step.success:
                    review_insights = step.output_data.get("review_insights")
            
            # Step 4: Music Recommendation Engine
            recommendations = None
            if request.enable_recommendations:
                self.orchestration_logger.log_module_start(execution_id, "recommendation_generation", 4)
                step = await self._execute_recommendation_generation(
                    request, intent, parsed_query, memory, review_insights, pipeline_steps, execution_id
                )
                self.orchestration_logger.log_module_complete(
                    execution_id, "recommendation_generation", step.success,
                    step.output_data, step.error_message
                )
                if step.success:
                    recommendations = step.output_data.get("recommendations")
            
            # Step 5: Explainability Engine
            explanations = None
            if request.enable_explanations and recommendations:
                self.orchestration_logger.log_module_start(execution_id, "explanation_generation", 5)
                step = await self._execute_explanation_generation(
                    request, recommendations, pipeline_steps, execution_id
                )
                self.orchestration_logger.log_module_complete(
                    execution_id, "explanation_generation", step.success,
                    step.output_data, step.error_message
                )
                if step.success:
                    explanations = step.output_data.get("explanations")
            
            # Step 6: Response Generation
            self.orchestration_logger.log_module_start(execution_id, "response_generation", 6)
            step = await self._execute_response_generation(
                request, intent, parsed_query, memory, review_insights, recommendations, pipeline_steps, execution_id
            )
            self.orchestration_logger.log_module_complete(
                execution_id, "response_generation", step.success,
                step.output_data, step.error_message
            )
            if not step.success:
                self.orchestration_logger.log_failure(
                    execution_id, "response_generation", "StepFailure",
                    step.error_message or "Unknown error"
                )
                return self._build_error_response(request, pipeline_steps, start_time, step.error_message, execution_id)
            
            response_text = step.output_data.get("response")
            
            # Log API latency for response generation
            if step.duration_ms:
                self.orchestration_logger.log_api_latency(
                    execution_id, "groq_api", step.duration_ms, True
                )
            
            # Build success response
            total_time = (time.time() - start_time) * 1000
            
            # Log pipeline completion
            self.orchestration_logger.log_pipeline_complete(
                execution_id, True, total_time, "completed"
            )
            
            return OrchestrationResponse(
                user_id=request.user_id,
                session_id=request.session_id,
                query=request.query,
                response=response_text,
                intent=intent,
                parsed_query=parsed_query,
                recommendations=recommendations,
                explanations=explanations,
                review_insights=review_insights,
                pipeline_steps=pipeline_steps,
                total_execution_time_ms=total_time,
                success=True
            )
            
        except Exception as e:
            logger.error(
                "Orchestration pipeline failed",
                user_id=request.user_id,
                error=str(e)
            )
            self.orchestration_logger.log_failure(
                execution_id, "orchestrator", "Exception", str(e)
            )
            self.orchestration_logger.log_pipeline_complete(
                execution_id, False, (time.time() - start_time) * 1000, "failed"
            )
            return self._build_error_response(request, pipeline_steps, start_time, str(e), execution_id)
    
    async def _execute_conversation_engine(
        self,
        request: OrchestrationRequest,
        pipeline_steps: List[PipelineStep],
        execution_id: str
    ) -> PipelineStep:
        """Execute Conversation Engine step."""
        step = PipelineStep(
            step_name="conversation_engine",
            step_order=1,
            status="running",
            started_at=datetime.utcnow()
        )
        pipeline_steps.append(step)
        
        try:
            # Intent Recognition
            intent_result = await self.conversation_engine["intent_recognizer"].recognize(
                request.query,
                request.conversation_history
            )
            
            # Query Parsing
            parsed_query = await self.conversation_engine["query_parser"].parse(
                request.query,
                intent_result.intent
            )
            
            step.status = "completed"
            step.completed_at = datetime.utcnow()
            step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000
            step.output_data = {
                "intent": intent_result.intent,
                "intent_confidence": intent_result.confidence,
                "parsed_query": parsed_query.dict()
            }
            step.success = True
            
            logger.info("Conversation engine completed", intent=intent_result.intent)
            
        except Exception as e:
            step.status = "failed"
            step.completed_at = datetime.utcnow()
            step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000
            step.error_message = str(e)
            step.success = False
            
            logger.error("Conversation engine failed", error=str(e))
        
        return step
    
    async def _execute_conversation_memory(
        self,
        request: OrchestrationRequest,
        pipeline_steps: List[PipelineStep],
        execution_id: str
    ) -> PipelineStep:
        """Execute Conversation Memory step."""
        step = PipelineStep(
            step_name="conversation_memory",
            step_order=2,
            status="running",
            started_at=datetime.utcnow()
        )
        pipeline_steps.append(step)
        
        try:
            # Retrieve conversation memory
            memory = await self.conversation_memory.get_user_memory(request.user_id)
            
            step.status = "completed"
            step.completed_at = datetime.utcnow()
            step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000
            step.output_data = {
                "memory": memory.dict() if memory else {}
            }
            step.success = True
            
            logger.info("Conversation memory retrieved")
            
        except Exception as e:
            step.status = "failed"
            step.completed_at = datetime.utcnow()
            step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000
            step.error_message = str(e)
            step.success = False
            
            # Memory failure is not critical - continue with empty memory
            step.output_data = {"memory": {}}
            step.status = "completed"
            step.success = True
            
            logger.warning("Conversation memory failed, using empty memory", error=str(e))
        
        return step
    
    async def _execute_review_insight_retrieval(
        self,
        request: OrchestrationRequest,
        pipeline_steps: List[PipelineStep],
        execution_id: str
    ) -> PipelineStep:
        """Execute Review Insight Retrieval step."""
        step = PipelineStep(
            step_name="review_insight_retrieval",
            step_order=3,
            status="running",
            started_at=datetime.utcnow()
        )
        pipeline_steps.append(step)
        
        try:
            # Fetch review insights
            executive_report = await self.review_client.get_executive_report()
            pain_points = await self.review_client.get_pain_points(severity_threshold=0.5)
            product_insights = await self.review_client.get_product_insights(actionable_only=True)
            
            review_insights = {
                "executive_report": executive_report.dict() if executive_report else None,
                "pain_points": [pp.dict() for pp in pain_points],
                "product_insights": [pi.dict() for pi in product_insights]
            }
            
            step.status = "completed"
            step.completed_at = datetime.utcnow()
            step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000
            step.output_data = {
                "review_insights": review_insights
            }
            step.success = True
            
            logger.info("Review insights retrieved")
            
        except Exception as e:
            step.status = "failed"
            step.completed_at = datetime.utcnow()
            step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000
            step.error_message = str(e)
            step.success = False
            
            # Review insights failure is not critical - continue without insights
            step.output_data = {"review_insights": None}
            step.status = "completed"
            step.success = True
            
            logger.warning("Review insight retrieval failed, continuing without insights", error=str(e))
        
        return step
    
    async def _execute_recommendation_generation(
        self,
        request: OrchestrationRequest,
        intent: str,
        parsed_query: Dict[str, Any],
        memory: Dict[str, Any],
        review_insights: Optional[Dict[str, Any]],
        pipeline_steps: List[PipelineStep],
        execution_id: str
    ) -> PipelineStep:
        """Execute Music Recommendation Engine step."""
        step = PipelineStep(
            step_name="recommendation_generation",
            step_order=4,
            status="running",
            started_at=datetime.utcnow()
        )
        pipeline_steps.append(step)
        
        try:
            # Build recommendation request
            from phase2_music_recommendation_engine.schemas import RecommendationRequest
            
            rec_request = RecommendationRequest(
                user_id=request.user_id,
                session_id=request.session_id,
                user_intent=intent,
                mood=parsed_query.get("mood"),
                activity=parsed_query.get("activity"),
                discovery_goal=parsed_query.get("discovery_preference", "balanced"),
                preferred_genres=parsed_query.get("genres", []),
                preferred_artists=parsed_query.get("artists", []),
                energy_level=parsed_query.get("energy_level"),
                popularity_filter=parsed_query.get("popularity_filter"),
                previously_recommended_songs=memory.get("previously_recommended_songs", []),
                previously_recommended_artists=memory.get("previously_recommended_artists", []),
                discovery_history=memory.get("discovery_history", []),
                recently_discussed_genres=memory.get("recently_discussed_genres", []),
                limit=request.max_recommendations,
                user_segment_id=memory.get("user_segment"),
                review_insights_enabled=request.enable_review_insights
            )
            
            # Generate recommendations
            response = await self.recommendation_engine.generate_recommendations(rec_request)
            
            recommendations = [
                {
                    "track": rec.track.dict(),
                    "confidence": rec.confidence,
                    "explanation": rec.explanation,
                    "strategies_used": rec.strategies_used,
                    "metadata": rec.metadata
                }
                for rec in response.recommendations
            ]
            
            step.status = "completed"
            step.completed_at = datetime.utcnow()
            step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000
            step.output_data = {
                "recommendations": recommendations,
                "strategies_executed": response.strategies_executed
            }
            step.success = True
            
            logger.info("Recommendations generated", count=len(recommendations))
            
        except Exception as e:
            step.status = "failed"
            step.completed_at = datetime.utcnow()
            step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000
            step.error_message = str(e)
            step.success = False
            
            logger.error("Recommendation generation failed", error=str(e))
        
        return step
    
    async def _execute_explanation_generation(
        self,
        request: OrchestrationRequest,
        recommendations: List[Dict[str, Any]],
        pipeline_steps: List[PipelineStep],
        execution_id: str
    ) -> PipelineStep:
        """Execute Explainability Engine step."""
        step = PipelineStep(
            step_name="explanation_generation",
            step_order=5,
            status="running",
            started_at=datetime.utcnow()
        )
        pipeline_steps.append(step)
        
        try:
            # Explanations are already generated by the recommendation engine
            # This step is a placeholder for additional explanation processing if needed
            explanations = [
                rec.get("metadata", {}).get("detailed_explanation")
                for rec in recommendations
                if rec.get("metadata", {}).get("detailed_explanation")
            ]
            
            step.status = "completed"
            step.completed_at = datetime.utcnow()
            step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000
            step.output_data = {
                "explanations": explanations
            }
            step.success = True
            
            logger.info("Explanations generated", count=len(explanations))
            
        except Exception as e:
            step.status = "failed"
            step.completed_at = datetime.utcnow()
            step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000
            step.error_message = str(e)
            step.success = False
            
            # Explanation failure is not critical
            step.output_data = {"explanations": []}
            step.status = "completed"
            step.success = True
            
            logger.warning("Explanation generation failed", error=str(e))
        
        return step
    
    async def _execute_response_generation(
        self,
        request: OrchestrationRequest,
        intent: str,
        parsed_query: Dict[str, Any],
        memory: Dict[str, Any],
        review_insights: Optional[Dict[str, Any]],
        recommendations: Optional[List[Dict[str, Any]]],
        pipeline_steps: List[PipelineStep],
        execution_id: str
    ) -> PipelineStep:
        """Execute Response Generation step."""
        step = PipelineStep(
            step_name="response_generation",
            step_order=6,
            status="running",
            started_at=datetime.utcnow()
        )
        pipeline_steps.append(step)
        
        try:
            # Build context for response generator
            context = {
                "current_mood": parsed_query.get("mood"),
                "current_activity": parsed_query.get("activity"),
                "current_goal": parsed_query.get("discovery_preference"),
                "recent_genres": parsed_query.get("genres", []),
                "recent_artists": parsed_query.get("artists", []),
                "energy_level": parsed_query.get("energy_level"),
                "popularity_filter": parsed_query.get("popularity_filter")
            }
            
            # Convert recommendations to ResponseGenerator format
            from phase1_ai_conversation_engine.response_generator.response_schemas import Recommendation
            rec_objects = []
            if recommendations:
                rec_objects = [
                    Recommendation(
                        artist=rec["track"]["artist_name"],
                        track=rec["track"]["name"],
                        explanation=rec["explanation"]
                    )
                    for rec in recommendations
                ]
            
            # Generate response
            response = await self.response_generator.generate(
                query=request.query,
                intent=intent,
                context=context,
                recommendations=rec_objects,
                memory=memory,
                review_insights=review_insights,
                user_id=request.user_id,
                session_id=request.session_id
            )
            
            step.status = "completed"
            step.completed_at = datetime.utcnow()
            step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000
            step.output_data = {
                "response": response.content,
                "confidence": response.confidence
            }
            step.success = True
            
            logger.info("Response generated")
            
        except Exception as e:
            step.status = "failed"
            step.completed_at = datetime.utcnow()
            step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000
            step.error_message = str(e)
            step.success = False
            
            logger.error("Response generation failed", error=str(e))
        
        return step
    
    def _build_error_response(
        self,
        request: OrchestrationRequest,
        pipeline_steps: List[PipelineStep],
        start_time: float,
        error_message: str,
        execution_id: Optional[str] = None
    ) -> OrchestrationResponse:
        """Build error response."""
        total_time = (time.time() - start_time) * 1000
        
        return OrchestrationResponse(
            user_id=request.user_id,
            session_id=request.session_id,
            query=request.query,
            response="I apologize, but I encountered an error processing your request. Please try again.",
            pipeline_steps=pipeline_steps,
            total_execution_time_ms=total_time,
            success=False,
            error_message=error_message
        )


class MockOrchestrator:
    """Mock orchestrator for testing."""
    
    def __init__(self):
        self.orchestration_logger = MockOrchestrationLogger()
    
    async def orchestrate(self, request: OrchestrationRequest) -> OrchestrationResponse:
        """Mock orchestration."""
        start_time = time.time()
        pipeline_id = f"pipeline_{request.user_id}_{request.session_id}_{int(start_time * 1000)}"
        
        # Log execution start
        execution_id = self.orchestration_logger.log_execution_start(
            user_id=request.user_id,
            session_id=request.session_id,
            query=request.query,
            pipeline_id=pipeline_id
        )
        
        pipeline_steps = [
            PipelineStep(
                step_name="conversation_engine",
                step_order=1,
                status="completed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                duration_ms=100,
                output_data={"intent": "DISCOVER_NEW_ARTISTS", "parsed_query": {}},
                success=True
            ),
            PipelineStep(
                step_name="conversation_memory",
                step_order=2,
                status="completed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                duration_ms=50,
                output_data={"memory": {}},
                success=True
            ),
            PipelineStep(
                step_name="review_insight_retrieval",
                step_order=3,
                status="completed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                duration_ms=75,
                output_data={"review_insights": None},
                success=True
            ),
            PipelineStep(
                step_name="recommendation_generation",
                step_order=4,
                status="completed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                duration_ms=200,
                output_data={"recommendations": [], "strategies_executed": []},
                success=True
            ),
            PipelineStep(
                step_name="explanation_generation",
                step_order=5,
                status="completed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                duration_ms=50,
                output_data={"explanations": []},
                success=True
            ),
            PipelineStep(
                step_name="response_generation",
                step_order=6,
                status="completed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                duration_ms=150,
                output_data={"response": "Mock response for testing", "confidence": 0.8},
                success=True
            )
        ]
        
        total_time = (time.time() - start_time) * 1000
        
        # Log pipeline completion
        self.orchestration_logger.log_pipeline_complete(
            execution_id, True, total_time, "completed"
        )
        
        return OrchestrationResponse(
            user_id=request.user_id,
            session_id=request.session_id,
            query=request.query,
            response="Mock response: I'd love to help you discover new music! Based on your preferences, I can suggest some hidden gems.",
            intent="DISCOVER_NEW_ARTISTS",
            parsed_query={},
            recommendations=[],
            explanations=[],
            review_insights=None,
            pipeline_steps=pipeline_steps,
            total_execution_time_ms=total_time,
            success=True
        )
