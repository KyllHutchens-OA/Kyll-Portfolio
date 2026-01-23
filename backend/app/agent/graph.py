"""
AFL Analytics Agent - LangGraph Workflow

Defines the agent workflow: UNDERSTAND → PLAN → EXECUTE → RESPOND
"""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from openai import OpenAI
import os
import logging
from dotenv import load_dotenv

from app.agent.state import AgentState, WorkflowStep, QueryIntent
from app.agent.tools import DatabaseTool, StatisticsTool
from app.analytics.query_builder import QueryBuilder
from app.analytics.entity_resolver import EntityResolver, MetricResolver
from app.visualization import PlotlyBuilder
from app.visualization.plotly_builder import ChartHelper

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class AFLAnalyticsAgent:
    """
    LangGraph-based agent for AFL analytics queries.

    Workflow:
    1. UNDERSTAND - Parse user query, extract intent and entities
    2. PLAN - Determine analysis steps required
    3. EXECUTE - Run SQL queries and compute statistics
    4. RESPOND - Format natural language response
    """

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("understand", self.understand_node)
        workflow.add_node("plan", self.plan_node)
        workflow.add_node("execute", self.execute_node)
        workflow.add_node("visualize", self.visualize_node)
        workflow.add_node("respond", self.respond_node)

        # Add edges
        workflow.add_edge("understand", "plan")
        workflow.add_edge("plan", "execute")

        # Conditional edge: visualize if needed, otherwise go to respond
        workflow.add_conditional_edges(
            "execute",
            lambda state: "visualize" if state.get("requires_visualization") and state.get("query_results") is not None and len(state.get("query_results", [])) > 0 else "respond",
            {
                "visualize": "visualize",
                "respond": "respond"
            }
        )

        workflow.add_edge("visualize", "respond")
        workflow.add_edge("respond", END)

        # Set entry point
        workflow.set_entry_point("understand")

        return workflow.compile()

    async def run(self, user_query: str, conversation_id: str = None) -> AgentState:
        """
        Run the agent workflow on a user query.

        Args:
            user_query: Natural language question
            conversation_id: Optional conversation ID

        Returns:
            Final agent state with response
        """
        initial_state = AgentState(
            user_query=user_query,
            conversation_id=conversation_id,
            entities={},
            needs_clarification=False,
            analysis_plan=[],
            requires_visualization=False,
            sql_validated=False,
            statistical_analysis={},
            errors=[],
            current_step=WorkflowStep.UNDERSTAND
        )

        final_state = await self.graph.ainvoke(initial_state)
        return final_state

    # ==================== WORKFLOW NODES ====================

    async def understand_node(self, state: AgentState) -> AgentState:
        """
        UNDERSTAND node: Parse user query and extract intent/entities.

        Updates:
        - intent
        - entities
        - thinking_message
        """
        state["current_step"] = WorkflowStep.UNDERSTAND
        state["thinking_message"] = "🔍 Understanding your question..."

        logger.info(f"UNDERSTAND: Processing query: {state['user_query']}")

        try:
            # Use GPT-5-nano to understand the query (Responses API)
            response = client.responses.create(
                model="gpt-5-nano",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": f"""You are an AFL analytics query analyzer. Parse the user's question and extract:
1. Intent: What type of analysis are they asking for?
2. Entities: What teams, players, seasons, or metrics are mentioned?

Intent Classification:
- "simple_stat": Single number/fact (e.g., "How many wins?", "What was the score?")
- "player_comparison": Comparing multiple players
- "team_analysis": Single team's performance over a SINGLE season/period
- "trend_analysis": TEMPORAL queries showing change over TIME (keywords: "over time", "across time", "year by year", "historical", "trend", "evolution", "since joining", "throughout history")

CRITICAL: If the query contains temporal keywords (over time, across time, year-by-year, historical, trend, since, evolution), the intent MUST be "trend_analysis".

Return a JSON object with:
{{
  "intent": "simple_stat" | "player_comparison" | "team_analysis" | "trend_analysis",
  "entities": {{
    "teams": [...],
    "players": [...],
    "seasons": [...],
    "metrics": [...],
    "rounds": [...]
  }},
  "requires_visualization": true/false
}}

User question: {state["user_query"]}"""
                            }
                        ]
                    }
                ],
                text={"format": {"type": "json_object"}}
            )

            import json
            understanding = json.loads(response.output_text)

            state["intent"] = QueryIntent(understanding.get("intent", "unknown"))
            raw_entities = understanding.get("entities", {})

            # VALIDATE AND NORMALIZE ENTITIES using EntityResolver
            validation_result = EntityResolver.validate_entities(raw_entities)

            # Use corrected entities
            state["entities"] = validation_result["corrected_entities"]

            # Log warnings about entity resolution
            if validation_result["warnings"]:
                for warning in validation_result["warnings"]:
                    logger.warning(f"Entity resolution: {warning}")

            # If validation failed completely, set clarification flag
            if not validation_result["is_valid"] and validation_result["suggestions"]:
                state["needs_clarification"] = True
                state["clarification_question"] = validation_result["suggestions"][0]

            state["requires_visualization"] = understanding.get("requires_visualization", False)

            logger.info(f"Intent: {state['intent']}, Raw entities: {raw_entities}, Resolved entities: {state['entities']}")

        except Exception as e:
            logger.error(f"Error in UNDERSTAND node: {e}")
            state["errors"].append(f"Understanding error: {str(e)}")

        return state

    async def plan_node(self, state: AgentState) -> AgentState:
        """
        PLAN node: Determine analysis steps required.

        Updates:
        - analysis_plan
        - chart_type (if visualization needed)
        - thinking_message
        """
        state["current_step"] = WorkflowStep.PLAN
        state["thinking_message"] = "📋 Planning the analysis..."

        intent = state.get('intent', QueryIntent.SIMPLE_STAT)
        logger.info(f"PLAN: Creating analysis plan for intent: {intent}")

        try:
            # Simple rule-based planning for MVP
            # Can be enhanced with LLM-based planning later

            plan = []

            # Step 1: Query database
            plan.append("Query AFL database for relevant data")

            # Step 2: Analysis based on intent
            if intent == QueryIntent.PLAYER_COMPARISON:
                plan.append("Compare player statistics")
                state["requires_visualization"] = True  # Force visualization for comparisons

            elif intent == QueryIntent.TEAM_ANALYSIS:
                plan.append("Analyze team performance")
                state["requires_visualization"] = True  # Force visualization for team analysis

            elif intent == QueryIntent.TREND_ANALYSIS:
                plan.append("Calculate trends over time")
                state["requires_visualization"] = True  # Force visualization for trends

            else:  # simple_stat
                plan.append("Extract requested statistics")

            # Step 3: Visualization if needed
            if state.get("requires_visualization", False):
                plan.append("Generate visualization")

            state["analysis_plan"] = plan

            logger.info(f"Analysis plan: {plan}")

        except Exception as e:
            logger.error(f"Error in PLAN node: {e}")
            state["errors"].append(f"Planning error: {str(e)}")

        return state

    async def execute_node(self, state: AgentState) -> AgentState:
        """
        EXECUTE node: Run SQL queries and compute statistics.

        Updates:
        - sql_query
        - sql_validated
        - query_results
        - statistical_analysis
        - thinking_message
        """
        state["current_step"] = WorkflowStep.EXECUTE
        state["thinking_message"] = "🔨 Generating SQL query..."

        logger.info("EXECUTE: Generating and running SQL query")

        try:
            # Step 1: Generate SQL from natural language
            # Use RESOLVED entities (normalized team names, validated seasons, etc.)
            sql_result = QueryBuilder.generate_sql(
                state["user_query"],
                context=state["entities"]  # These are now validated/normalized
            )

            if not sql_result["success"]:
                state["execution_error"] = sql_result["error"]
                state["errors"].append(sql_result["error"])
                state["thinking_message"] = f"❌ Error: {sql_result['error']}"
                return state

            state["sql_query"] = sql_result["sql"]
            logger.info(f"Generated SQL: {state['sql_query']}")

            # Step 2: Execute query
            state["thinking_message"] = "⚡ Querying AFL database (6,243 matches)..."
            db_result = DatabaseTool.query_database(state["sql_query"])

            if not db_result["success"]:
                state["execution_error"] = db_result["error"]
                state["errors"].append(db_result["error"])
                state["thinking_message"] = f"❌ Query failed: {db_result['error']}"
                return state

            state["sql_validated"] = True
            state["query_results"] = db_result["data"]

            logger.info(f"Query returned {db_result['rows_returned']} rows")
            state["thinking_message"] = f"✅ Found {db_result['rows_returned']} results"

            # Step 3: Compute statistics if needed
            if len(db_result["data"]) > 0 and state.get("intent") != QueryIntent.SIMPLE_STAT:
                state["thinking_message"] = "📊 Calculating statistics..."
                stats_result = StatisticsTool.compute_statistics(
                    db_result["data"],
                    analysis_type="average"
                )

                if stats_result["success"]:
                    state["statistical_analysis"] = stats_result

        except Exception as e:
            logger.error(f"Error in EXECUTE node: {e}")
            state["execution_error"] = str(e)
            state["errors"].append(f"Execution error: {str(e)}")
            state["thinking_message"] = f"❌ Error: {str(e)}"

        return state

    async def visualize_node(self, state: AgentState) -> AgentState:
        """
        VISUALIZE node: Generate Plotly chart specification.

        Updates:
        - visualization_spec
        - thinking_message
        """
        state["current_step"] = WorkflowStep.VISUALIZE
        state["thinking_message"] = "📈 Creating visualization..."

        logger.info("VISUALIZE: Generating chart")

        try:
            # Get data and intent
            data = state["query_results"]
            intent = state.get("intent")
            entities = state.get("entities", {})

            # VALIDATION: Check if we have enough data points for a useful chart
            MIN_DATA_POINTS = 2  # Need at least 2 points for a trend
            if len(data) < MIN_DATA_POINTS:
                logger.warning(f"Insufficient data for visualization: {len(data)} rows (need at least {MIN_DATA_POINTS})")
                state["thinking_message"] = f"⚠️ Not enough data points for chart ({len(data)} rows)"
                # Skip visualization - will go to respond node without chart
                return state

            # Auto-detect x and y columns
            numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
            non_numeric_cols = data.select_dtypes(exclude=['number']).columns.tolist()
            all_cols = data.columns.tolist()

            # INTELLIGENT CHART TYPE SELECTION
            chart_type = PlotlyBuilder._select_chart_type(data, intent, all_cols)

            params = {}

            # Smart column detection based on common AFL data patterns
            # Priority for X-axis:
            # - For TREND queries: season > year > match_date > round
            # - For PERFORMANCE queries: round > match_date > season
            x_col = None

            if intent == QueryIntent.TREND_ANALYSIS:
                # Temporal queries prioritize time periods
                if 'season' in all_cols:
                    x_col = 'season'
                elif 'year' in all_cols:
                    x_col = 'year'
                elif 'match_date' in all_cols:
                    x_col = 'match_date'
                elif 'round' in all_cols:
                    x_col = 'round'
                elif len(non_numeric_cols) > 0:
                    x_col = non_numeric_cols[0]
            else:
                # Performance/single-season queries prioritize rounds
                if 'round' in all_cols:
                    x_col = 'round'
                elif 'match_date' in all_cols:
                    x_col = 'match_date'
                elif 'season' in all_cols:
                    x_col = 'season'
                elif len(non_numeric_cols) > 0:
                    x_col = non_numeric_cols[0]

            # Priority for Y-axis: margin > team_score > wins > first numeric
            y_col = None
            if 'margin' in all_cols:
                y_col = 'margin'
            elif 'team_score' in all_cols:
                y_col = 'team_score'
            elif 'wins' in all_cols:
                y_col = 'wins'
            elif len(numeric_cols) > 0:
                y_col = numeric_cols[0]

            if x_col and y_col:
                params["x_col"] = x_col
                params["y_col"] = y_col

                # Group by result (Win/Loss) if available
                if 'result' in all_cols and chart_type == 'line':
                    params["group_col"] = 'result'

            # Generate smart title
            params["title"] = ChartHelper.generate_chart_title(
                intent=str(intent),
                entities=entities,
                metrics=entities.get("metrics", []),
                data_cols=all_cols
            )

            # Generate chart
            chart_spec = PlotlyBuilder.generate_chart(data, chart_type, params)

            state["visualization_spec"] = chart_spec

            logger.info(f"Chart generated: {chart_type}")
            state["thinking_message"] = f"✅ Chart created ({chart_type})"

        except Exception as e:
            logger.error(f"Error in VISUALIZE node: {e}")
            state["errors"].append(f"Visualization error: {str(e)}")
            state["thinking_message"] = f"⚠️ Skipping visualization: {str(e)}"

        return state

    async def respond_node(self, state: AgentState) -> AgentState:
        """
        RESPOND node: Format natural language response.

        Updates:
        - natural_language_summary
        - confidence
        - thinking_message
        """
        state["current_step"] = WorkflowStep.RESPOND
        state["thinking_message"] = "✍️ Writing response..."

        logger.info("RESPOND: Generating natural language response")

        try:
            # Check for errors
            if state.get("execution_error"):
                state["natural_language_summary"] = (
                    "I encountered an issue while analyzing your query. "
                    "Could you rephrase your question?"
                )
                state["confidence"] = 0.0
                return state

            # Check if we have results
            if state.get("query_results") is None or len(state["query_results"]) == 0:
                # Provide helpful suggestions based on what went wrong
                raw_query = state.get("user_query", "")
                suggestions = []

                # Check if there were entity resolution issues
                if state.get("needs_clarification"):
                    suggestions.append(state.get("clarification_question", ""))

                # Suggest checking team names
                if "entities" in state and "teams" in state["entities"]:
                    if not state["entities"]["teams"]:
                        suggestions.append(
                            f"Available teams: Adelaide, Brisbane Lions, Carlton, Collingwood, Essendon, "
                            f"Fremantle, Geelong, Gold Coast, GWS, Hawthorn, Melbourne, North Melbourne, "
                            f"Port Adelaide, Richmond, St Kilda, Sydney, West Coast, Western Bulldogs"
                        )

                # Check if query asked for player stats
                if "player" in raw_query.lower() or "stats" in raw_query.lower():
                    suggestions.append(
                        "Note: Player statistics are not yet available - only match-level data (1990-2025) is currently loaded."
                    )

                suggestion_text = " ".join(suggestions) if suggestions else (
                    "Note: Player statistics are not yet available - only match-level data (1990-2025) is currently loaded."
                )

                state["natural_language_summary"] = (
                    f"I couldn't find any data matching your query. {suggestion_text}"
                )
                state["confidence"] = 0.3
                return state

            # Generate response using GPT-5-nano (Responses API)
            response = client.responses.create(
                model="gpt-5-nano",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": f"""You are an AFL analytics expert. Generate a natural language summary of the query results.

Guidelines:
- Be concise but informative
- Use Australian football terminology correctly
- Include specific numbers and statistics
- If the data shows interesting patterns, mention them
- Never mention SQL, databases, or technical details
- Write in a friendly, conversational tone

User asked: {state['user_query']}

Query results:
{state['query_results'].to_string() if len(state['query_results']) < 20 else state['query_results'].head(10).to_string()}

Generate a natural language summary:"""
                            }
                        ]
                    }
                ]
            )

            state["natural_language_summary"] = response.output_text.strip()
            state["confidence"] = 0.9
            state["sources"] = ["AFL Tables (1990-2025)"]
            state["thinking_message"] = "✅ Response complete!"

            logger.info("Response generated successfully")

        except Exception as e:
            logger.error(f"Error in RESPOND node: {e}")
            state["natural_language_summary"] = "I encountered an issue generating the response."
            state["confidence"] = 0.0
            state["errors"].append(f"Response error: {str(e)}")

        return state


# Global agent instance
agent = AFLAnalyticsAgent()
