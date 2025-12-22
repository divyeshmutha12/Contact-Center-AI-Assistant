"""
MariaDB Query Tool for Data Extraction Agent

This tool executes pre-configured MariaDB SQL queries to generate reports like agent activity report, etc.
This tool is the only tool that you need if you have to create certain type of fixed reports from MariaDB.

Output format:
- Tool returns: [DOWNLOAD:outputs/filename.xlsx]
- WebSocket handler transforms to full URL with session path
"""

import os
import json
import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from langchain.tools import tool
import pymysql
from pymysql.cursors import DictCursor
from openpyxl import Workbook

load_dotenv()
logger = logging.getLogger(__name__)


class MariaDBQueryExecutor:
    """
    MariaDB Query Executor - handles connection and query execution.
    READ-ONLY operations only for safety.
    """

    def __init__(self):
        self.host = os.getenv("MYSQL_HOST")
        self.user = os.getenv("MYSQL_USER")
        self.password = os.getenv("MYSQL_PASS")
        self.database = os.getenv("MYSQL_DB_NAME", "ccs_dev")
        self.connection = None

        if not all([self.host, self.user, self.password]):
            raise ValueError("MariaDB credentials not found in .env (MYSQL_HOST, MYSQL_USER, MYSQL_PASS)")

        logger.info(f"MariaDBQueryExecutor initialized for database: {self.database}")

    def connect(self):
        """Create READ-ONLY MariaDB connection."""
        if self.connection is not None:
            return

        self.connection = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            cursorclass=DictCursor,
            connect_timeout=10,
            read_timeout=300,
            charset='utf8mb4'
        )

        # Test connection
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        logger.info("MariaDB connection established (READ-ONLY mode)")

    def close(self):
        """Close MariaDB connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("MariaDB connection closed")

    def execute_query(self, query: str) -> list:
        """Execute SQL query and return results."""
        if self.connection is None:
            self.connect()

        with self.connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()

        logger.info(f"Query returned {len(results)} rows")
        return results


def load_mariadb_queries_config(config_path: str = "config/mariadb_queries.json") -> Dict:
    """Load MariaDB queries configuration from JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"MariaDB queries config not found: {config_path}")

    with open(config_path, "r") as f:
        return json.load(f)


def get_current_date_range() -> tuple:
    """Get current date start and end times."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today.strftime("%Y-%m-%d 00:00:00")
    end_date = today.strftime("%Y-%m-%d 23:59:59")
    return start_date, end_date


def apply_current_date_defaults(parameters: Dict) -> Dict:
    """Replace CURRENT_DATE placeholders with actual current date."""
    current_start, current_end = get_current_date_range()

    for key, value in parameters.items():
        if value == "{{CURRENT_DATE_START}}":
            parameters[key] = current_start
        elif value == "{{CURRENT_DATE_END}}":
            parameters[key] = current_end

    return parameters


def replace_placeholders(query: str, parameters: Dict) -> str:
    """Replace placeholders in SQL query with actual values."""
    result = query
    for param_name, value in parameters.items():
        placeholder = "{{" + param_name + "}}"
        if placeholder in result:
            # Escape single quotes in values for SQL safety
            if isinstance(value, str):
                safe_value = value.replace("'", "''")
                result = result.replace(placeholder, safe_value)
            else:
                result = result.replace(placeholder, str(value))
    return result


def format_cell_value(value: Any) -> Any:
    """Format a value for Excel cell."""
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')

    if isinstance(value, bytes):
        return value.decode('utf-8', errors='ignore')

    if isinstance(value, (int, float)) and abs(value) > 1000000:
        return str(int(value))

    return value


def create_mariadb_query_tool(session_id: str, session_folder: str):
    """
    Factory function to create a session-specific MariaDB query tool.

    Args:
        session_id: Unique session ID (ws_id)
        session_folder: Absolute path to session folder
    """

    # Initialize query executor (shared across tool calls)
    executor = MariaDBQueryExecutor()

    def generate_mariadb_reports(
        query_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        agent_id: Optional[int] = None,
        sme_id: Optional[int] = None,
        limit: Optional[int] = None,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Generate reports by executing pre-configured MariaDB queries and exporting results to Excel.

        This tool runs READ-ONLY queries against MariaDB and exports results to Excel.
        Queries are defined in config/mariadb_queries.json and can be customized via parameters.

        Args:
            query_name: Name of the report/query to generate (e.g., 'agent_activity',
                       'agent_break_details', 'agent_performance_summary', 'agent_status_report').
                       Use 'list' to see all available reports.
            start_date: Override start date (format: YYYY-MM-DD HH:MM:SS).
                       If not provided, uses current date.
            end_date: Override end date (format: YYYY-MM-DD HH:MM:SS).
                     If not provided, uses current date.
            agent_id: Filter by specific agent ID
            sme_id: Override SME ID filter (used in agent_status_report)
            limit: Limit number of results
            output_filename: Custom filename for Excel output (default: {query_name}_report.xlsx)

        Returns:
            Download URL for the Excel file with report data
        """
        try:
            logger.info(f"[{session_id}] Executing MariaDB query: {query_name}")

            # Load queries config
            queries = load_mariadb_queries_config()

            # Handle list command
            if query_name.lower() == "list":
                query_list = []
                for name, config in queries.items():
                    desc = config.get("description", "No description")
                    params = list(config.get("parameters", {}).keys())
                    query_list.append(f"- **{name}**\n  Description: {desc}\n  Parameters: {params}")
                return "Available MariaDB queries:\n\n" + "\n\n".join(query_list)

            # Validate query name
            if query_name not in queries:
                available = ", ".join(queries.keys())
                return f"Error: Query '{query_name}' not found. Available queries: {available}"

            query_config = queries[query_name]

            # Build parameters
            parameters = query_config.get("parameters", {}).copy()

            # Apply current date defaults if configured
            if query_config.get("use_current_date_default", False):
                parameters = apply_current_date_defaults(parameters)

            # Apply parameter overrides
            if start_date:
                parameters["start_date"] = start_date
            if end_date:
                parameters["end_date"] = end_date
            if agent_id is not None:
                parameters["agent_id"] = agent_id
            if sme_id is not None:
                parameters["sme_id"] = sme_id

            actual_start_date = parameters.get("start_date", "N/A")
            actual_end_date = parameters.get("end_date", "N/A")

            # Build query with parameters
            query_template = query_config.get("query", "")
            query = replace_placeholders(query_template, parameters)

            # Add LIMIT if specified
            if limit is not None:
                query = query.rstrip(';') + f" LIMIT {limit}"

            logger.info(f"[{session_id}] Date range: {actual_start_date} to {actual_end_date}")

            # Execute query
            executor.connect()
            results = executor.execute_query(query)

            if not results:
                return f"Query '{query_name}' returned no results for date range {actual_start_date} to {actual_end_date}. Try adjusting the date range or filters."

            # Generate Excel file
            if not output_filename:
                output_filename = f"{query_name}_report.xlsx"
            if not output_filename.endswith('.xlsx'):
                output_filename = f"{output_filename}.xlsx"

            output_dir = os.path.join(session_folder, "outputs")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)

            # Create Excel workbook
            wb = Workbook(write_only=True)
            ws = wb.create_sheet(title="Report")

            # Get headers from first result
            if results:
                headers = list(results[0].keys())
                ws.append(headers)

                # Write data rows
                rows_written = 0
                for row in results:
                    row_data = [format_cell_value(row.get(key)) for key in headers]
                    ws.append(row_data)
                    rows_written += 1

            wb.save(output_path)
            wb.close()

            logger.info(f"[{session_id}] Excel saved: {output_path} ({rows_written} rows)")

            # Prepare top 5 records summary for agent
            summary_records = []
            for row in results[:5]:
                summary_record = {}
                for key, value in row.items():
                    summary_record[key] = format_cell_value(value)
                summary_records.append(summary_record)

            # Format summary as JSON string
            summary_json = json.dumps(summary_records, indent=2, default=str)

            relative_path = f"outputs/{output_filename}"

            response = f"""Report '{query_name}' generated successfully.

**Date Range:** {actual_start_date} to {actual_end_date}
**Total Records:** {rows_written}

**Top 5 Records Summary (for agent reference):**
```json
{summary_json}
```

**Full Report Download:**
[DOWNLOAD:{relative_path}]"""

            return response

        except FileNotFoundError as e:
            logger.error(f"[{session_id}] Config file not found: {e}")
            return f"Error: Configuration file not found. {str(e)}"
        except Exception as e:
            logger.error(f"[{session_id}] Query execution error: {e}", exc_info=True)
            return f"Error executing query: {str(e)}"

    # Return decorated tool
    return tool(generate_mariadb_reports)
