"""
AFL Analytics Agent - Intelligent Chart Selector

Uses LLM to intelligently select optimal chart type, columns, and configuration
based on user query and data characteristics.
"""
from typing import Dict, Any, Optional, List
import pandas as pd
import logging
import json
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ChartSelector:
    """
    Intelligently selects chart type and configuration using LLM + heuristics.

    Decision flow:
    1. Quick heuristics check for obvious cases (single value, empty data)
    2. LLM analysis for complex/ambiguous cases
    3. Validation and fallback to sensible defaults
    """

    # Chart type descriptions for LLM
    CHART_TYPES = {
        "line": "Shows trends over time or sequential data. Best for temporal analysis.",
        "bar": "Compares values across categories. Best for rankings, top N, or category comparison.",
        "horizontal_bar": "Like bar but horizontal. Best for long category names or rankings.",
        "grouped_bar": "Compares multiple metrics across categories side-by-side.",
        "stacked_bar": "Shows composition/parts of a whole across categories.",
        "scatter": "Shows relationship/correlation between two numeric variables.",
        "pie": "Shows proportions of a whole. Best for 3-7 categories only.",
        "box": "Shows distribution and outliers. Best for statistical analysis.",
    }

    @classmethod
    def select_chart_configuration(
        cls,
        user_query: str,
        data: pd.DataFrame,
        intent: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Intelligently select optimal chart configuration.

        Args:
            user_query: Original user question
            data: Query results DataFrame
            intent: Classified intent (TREND_ANALYSIS, etc.)
            entities: Extracted entities (teams, metrics, etc.)

        Returns:
            Dictionary with:
            - chart_type: str
            - x_col: str
            - y_col: str or List[str]
            - group_col: Optional[str]
            - aggregation: Optional[str]
            - orientation: Optional[str]
            - reasoning: str (why this chart was chosen)
        """
        try:
            # Quick heuristics for obvious cases
            quick_result = cls._quick_heuristics(data, intent)
            if quick_result:
                logger.info(f"Chart selection via quick heuristics: {quick_result['chart_type']}")
                return quick_result

            # Use LLM for intelligent selection
            llm_result = cls._llm_chart_selection(user_query, data, intent, entities)

            if llm_result:
                # Validate LLM result
                validated = cls._validate_and_enhance(llm_result, data)
                logger.info(f"Chart selection via LLM: {validated['chart_type']}")
                return validated

            # Fallback to rule-based
            logger.warning("LLM chart selection failed, using fallback")
            return cls._fallback_selection(data, intent)

        except Exception as e:
            logger.error(f"Error in chart selection: {e}")
            return cls._fallback_selection(data, intent)

    @classmethod
    def _quick_heuristics(
        cls,
        data: pd.DataFrame,
        intent: str
    ) -> Optional[Dict[str, Any]]:
        """
        Quick heuristics for obvious cases to avoid LLM call.

        Returns None if case is not obvious.
        """
        # Single row -> no chart needed
        if len(data) <= 1:
            return None

        # Single numeric column with temporal dimension -> line chart
        numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
        temporal_cols = [col for col in data.columns if col in ['season', 'year', 'match_date', 'round']]

        if len(numeric_cols) == 1 and len(temporal_cols) == 1:
            return {
                "chart_type": "line",
                "x_col": temporal_cols[0],
                "y_col": numeric_cols[0],
                "group_col": None,
                "reasoning": "Single metric over time - line chart is optimal",
                "confidence": "high"
            }

        # 2-5 rows, no temporal dimension -> bar chart
        if 2 <= len(data) <= 5 and not temporal_cols:
            non_numeric = data.select_dtypes(exclude=['number']).columns.tolist()
            if non_numeric and numeric_cols:
                return {
                    "chart_type": "bar",
                    "x_col": non_numeric[0],
                    "y_col": numeric_cols[0],
                    "group_col": None,
                    "reasoning": "Few categories to compare - bar chart is optimal",
                    "confidence": "high"
                }

        # Not obvious, need LLM analysis
        return None

    @classmethod
    def _llm_chart_selection(
        cls,
        user_query: str,
        data: pd.DataFrame,
        intent: str,
        entities: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Use LLM to intelligently select chart configuration.

        Args:
            user_query: Original question
            data: Query results
            intent: Classified intent
            entities: Extracted entities

        Returns:
            Chart configuration dict or None if LLM fails
        """
        try:
            # Prepare data summary for LLM
            data_summary = cls._summarize_data_for_llm(data)

            # Available chart types
            chart_types_desc = "\n".join([
                f"- {name}: {desc}"
                for name, desc in cls.CHART_TYPES.items()
            ])

            prompt = f"""You are a data visualization expert. Analyze the user's question and data to select the optimal chart type and configuration.

User Question: "{user_query}"

Query Intent: {intent}

Data Summary:
- Rows: {len(data)}
- Columns: {', '.join(data.columns.tolist())}
- Numeric columns: {', '.join(data.select_dtypes(include=['number']).columns.tolist())}
- Non-numeric columns: {', '.join(data.select_dtypes(exclude=['number']).columns.tolist())}

Sample Data (first 3 rows):
{data.head(3).to_string()}

Available Chart Types:
{chart_types_desc}

Task: Select the BEST chart type and configuration for this query. Consider:
1. What is the user trying to understand? (trend, comparison, correlation, distribution, composition)
2. What type of data do we have? (time series, categories, continuous variables)
3. How many data points? (affects chart readability)
4. Are there multiple metrics to compare?
5. Is there a natural grouping variable?

Return a JSON object with:
{{
  "chart_type": "line|bar|horizontal_bar|grouped_bar|scatter|pie",
  "x_col": "column name for x-axis",
  "y_col": "column name(s) for y-axis (string or list)",
  "group_col": "optional column to group/color by",
  "reasoning": "2-3 sentence explanation of why this chart is optimal",
  "confidence": "high|medium|low",
  "alternative": "optional alternative chart type if user wants different view"
}}

Important:
- Choose chart type that directly answers the user's question
- Prefer simpler charts when appropriate (don't over-complicate)
- For "over time" queries, use line charts
- For "top N" or "compare" queries, use bar charts
- For "correlation" or "relationship" queries, use scatter plots
- Consider readability (don't chart 20 metrics on one chart)
"""

            # Call GPT-5-nano for fast decision
            response = client.responses.create(
                model="gpt-5-nano",
                input=[{
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}]
                }],
                text={"format": {"type": "json_object"}}
            )

            # Parse LLM response
            result = json.loads(response.output_text)

            logger.info(f"LLM chart selection: {result.get('chart_type')} (confidence: {result.get('confidence')})")
            logger.info(f"Reasoning: {result.get('reasoning')}")

            return result

        except Exception as e:
            logger.error(f"LLM chart selection error: {e}")
            return None

    @classmethod
    def _summarize_data_for_llm(cls, data: pd.DataFrame) -> Dict[str, Any]:
        """Create concise data summary for LLM."""
        return {
            "rows": len(data),
            "columns": data.columns.tolist(),
            "numeric_columns": data.select_dtypes(include=['number']).columns.tolist(),
            "categorical_columns": data.select_dtypes(exclude=['number']).columns.tolist(),
            "sample": data.head(3).to_dict()
        }

    @classmethod
    def _validate_and_enhance(
        cls,
        llm_result: Dict[str, Any],
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Validate LLM result and add missing fields.

        Args:
            llm_result: Raw LLM output
            data: Query results

        Returns:
            Validated and enhanced configuration
        """
        # Ensure required fields exist
        chart_type = llm_result.get("chart_type", "bar")
        x_col = llm_result.get("x_col")
        y_col = llm_result.get("y_col")

        # Validate columns exist in data
        if x_col and x_col not in data.columns:
            logger.warning(f"X column '{x_col}' not found, using first column")
            x_col = data.columns[0]

        if isinstance(y_col, str) and y_col not in data.columns:
            logger.warning(f"Y column '{y_col}' not found, using first numeric")
            numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
            y_col = numeric_cols[0] if numeric_cols else data.columns[1]

        # Validate group column
        group_col = llm_result.get("group_col")
        if group_col and group_col not in data.columns:
            logger.warning(f"Group column '{group_col}' not found, ignoring")
            group_col = None

        return {
            "chart_type": chart_type,
            "x_col": x_col,
            "y_col": y_col,
            "group_col": group_col,
            "reasoning": llm_result.get("reasoning", ""),
            "confidence": llm_result.get("confidence", "medium"),
            "alternative": llm_result.get("alternative")
        }

    @classmethod
    def _fallback_selection(
        cls,
        data: pd.DataFrame,
        intent: str
    ) -> Dict[str, Any]:
        """
        Fallback to simple rule-based selection.

        Used when LLM fails or for safety.
        """
        numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
        non_numeric_cols = data.select_dtypes(exclude=['number']).columns.tolist()

        # Default: bar chart with first non-numeric as X, first numeric as Y
        x_col = non_numeric_cols[0] if non_numeric_cols else numeric_cols[0] if numeric_cols else data.columns[0]
        y_col = numeric_cols[0] if numeric_cols else data.columns[1] if len(data.columns) > 1 else data.columns[0]

        # Check for temporal dimension
        temporal_cols = ['season', 'year', 'match_date', 'round']
        has_temporal = any(col in data.columns for col in temporal_cols)

        chart_type = "line" if (has_temporal and len(data) > 3) else "bar"

        return {
            "chart_type": chart_type,
            "x_col": x_col,
            "y_col": y_col,
            "group_col": None,
            "reasoning": "Fallback selection - basic heuristics applied",
            "confidence": "low"
        }
