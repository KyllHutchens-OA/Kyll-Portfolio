"""
AFL Analytics Agent - Tools

Tools that the LangGraph agent can use to accomplish tasks.
"""
from typing import Dict, Any, Optional
import pandas as pd
from sqlalchemy import text
from decimal import Decimal
import logging

from app.data.database import Session
from app.analytics.validators import SQLValidator

logger = logging.getLogger(__name__)


class DatabaseTool:
    """
    Tool for querying the AFL database.

    Security: All SQL queries are validated before execution to prevent injection.
    """

    @staticmethod
    def query_database(sql: str) -> Dict[str, Any]:
        """
        Execute a validated SQL query and return results.

        Args:
            sql: SQL query string

        Returns:
            Dictionary with:
            - success: bool
            - data: DataFrame (if successful)
            - error: str (if failed)
            - rows_returned: int
        """
        try:
            # Validate SQL
            is_valid, error_message = SQLValidator.validate(sql)

            if not is_valid:
                logger.warning(f"SQL validation failed: {error_message}")
                return {
                    "success": False,
                    "error": f"Query validation failed: {error_message}",
                    "data": None,
                    "rows_returned": 0
                }

            # Execute query
            session = Session()

            try:
                result = session.execute(text(sql))
                df = pd.DataFrame(result.fetchall(), columns=result.keys())

                # Convert Decimal types to float for JSON serialization
                if len(df) > 0:
                    for col in df.columns:
                        if df[col].dtype == 'object':
                            # Check if column contains Decimal objects
                            first_non_null = df[col].dropna().head(1)
                            if len(first_non_null) > 0 and isinstance(first_non_null.iloc[0], Decimal):
                                df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)

                logger.info(f"Query executed successfully: {len(df)} rows returned")

                return {
                    "success": True,
                    "data": df,
                    "error": None,
                    "rows_returned": len(df)
                }

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Database query error: {e}")
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "data": None,
                "rows_returned": 0
            }


class StatisticsTool:
    """
    Tool for computing statistics on data.

    Supports: averages, trends, comparisons, rankings.
    """

    @staticmethod
    def compute_statistics(
        data: pd.DataFrame,
        analysis_type: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compute statistics on the provided data.

        Args:
            data: Pandas DataFrame
            analysis_type: Type of analysis ("average", "trend", "comparison", "rank")
            params: Optional parameters for the analysis

        Returns:
            Dictionary with computed statistics
        """
        if params is None:
            params = {}

        try:
            if analysis_type == "average":
                return StatisticsTool._compute_averages(data, params)

            elif analysis_type == "trend":
                return StatisticsTool._compute_trends(data, params)

            elif analysis_type == "comparison":
                return StatisticsTool._compute_comparison(data, params)

            elif analysis_type == "rank":
                return StatisticsTool._compute_rankings(data, params)

            else:
                return {
                    "success": False,
                    "error": f"Unknown analysis type: {analysis_type}"
                }

        except Exception as e:
            logger.error(f"Statistics computation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def _compute_averages(data: pd.DataFrame, params: Dict) -> Dict[str, Any]:
        """Compute averages for specified columns."""
        numeric_cols = data.select_dtypes(include=['number']).columns.tolist()

        averages = {}
        for col in numeric_cols:
            averages[col] = {
                "mean": float(data[col].mean()),
                "median": float(data[col].median()),
                "std": float(data[col].std()),
                "min": float(data[col].min()),
                "max": float(data[col].max())
            }

        return {
            "success": True,
            "averages": averages,
            "row_count": len(data)
        }

    @staticmethod
    def _compute_trends(data: pd.DataFrame, params: Dict) -> Dict[str, Any]:
        """Compute trends over time."""
        # Placeholder - will implement rolling averages, momentum, etc.
        return {
            "success": True,
            "trends": {},
            "message": "Trend analysis not yet implemented"
        }

    @staticmethod
    def _compute_comparison(data: pd.DataFrame, params: Dict) -> Dict[str, Any]:
        """Compare entities (players, teams) across metrics."""
        # Placeholder - will implement comparisons
        return {
            "success": True,
            "comparison": {},
            "message": "Comparison analysis not yet implemented"
        }

    @staticmethod
    def _compute_rankings(data: pd.DataFrame, params: Dict) -> Dict[str, Any]:
        """Rank entities by specified metric."""
        # Placeholder - will implement rankings
        return {
            "success": True,
            "rankings": {},
            "message": "Ranking analysis not yet implemented"
        }
