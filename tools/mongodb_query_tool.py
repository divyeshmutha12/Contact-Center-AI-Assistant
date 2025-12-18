"""
MongoDB Query Tool for Data Extraction Agent

This tool executes pre-configured MongoDB aggregation queries to generate reports like incoming call report, outgoing call report, etc.
This tool is the only tool that you need if you have to create only certain type of fixed reports.

Output format:
- Tool returns: [DOWNLOAD:outputs/filename.xlsx]
- WebSocket handler transforms to full URL with session path
"""

import os
import json
import re
import copy
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from langchain.tools import tool
from pymongo import MongoClient, ReadPreference
from openpyxl import Workbook

load_dotenv()
logger = logging.getLogger(__name__)


class MongoDBQueryExecutor:
    """
    MongoDB Query Executor - handles connection and query execution.
    READ-ONLY operations only for safety.
    """

    def __init__(self):
        self.connection_string = os.getenv("MDB_MCP_CONNECTION_STRING")
        self.database_name = os.getenv("MONGODB_DATABASE", "ccs_dev")
        self.read_only = os.getenv("MDB_MCP_READ_ONLY", "true").lower() == "true"
        self.client: Optional[MongoClient] = None
        self.db = None

        if not self.connection_string:
            raise ValueError("MDB_MCP_CONNECTION_STRING not found in .env")

        logger.info(f"MongoDBQueryExecutor initialized for database: {self.database_name}")

    def connect(self):
        """Create READ-ONLY MongoDB connection."""
        if self.client is not None:
            return

        self.client = MongoClient(
            self.connection_string,
            readPreference='secondaryPreferred',
            serverSelectionTimeoutMS=10000
        )

        self.db = self.client.get_database(
            self.database_name,
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )

        # Test connection
        self.client.admin.command('ping')
        logger.info("MongoDB connection established (READ-ONLY mode)")

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("MongoDB connection closed")

    def execute_aggregation(self, collection_name: str, pipeline: List[Dict]) -> List[Dict]:
        """Execute aggregation pipeline on collection."""
        if self.db is None:
            self.connect()

        collection = self.db[collection_name]
        results = list(collection.aggregate(pipeline))
        logger.info(f"Query returned {len(results)} documents from {collection_name}")
        return results


def load_queries_config(config_path: str = "config/queries.json") -> Dict:
    """Load queries configuration from JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Queries config not found: {config_path}")

    with open(config_path, "r") as f:
        return json.load(f)


def parse_datetime_value(value: str) -> datetime:
    """Parse datetime string to datetime object."""
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return value


def replace_placeholders(obj: Any, parameters: Dict) -> Any:
    """Recursively replace placeholders in pipeline with actual values."""
    if isinstance(obj, str):
        match = re.match(r"^\{\{(\w+)\}\}$", obj)
        if match:
            param_name = match.group(1)
            if param_name in parameters:
                value = parameters[param_name]
                # Convert date strings to datetime objects
                if param_name in ["start_date", "end_date"] or "date" in param_name.lower():
                    if isinstance(value, str):
                        return parse_datetime_value(value)
                return value
        return obj
    elif isinstance(obj, dict):
        return {k: replace_placeholders(v, parameters) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_placeholders(item, parameters) for item in obj]
    else:
        return obj


def get_current_date_range() -> tuple:
    """Get current date start and end times."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today.strftime("%Y-%m-%dT00:00:00")
    end_date = today.strftime("%Y-%m-%dT23:59:59")
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


def build_pipeline(query_config: Dict, param_overrides: Optional[Dict] = None) -> List[Dict]:
    """Build aggregation pipeline with parameter substitution."""
    parameters = query_config.get("parameters", {}).copy()

    # Apply current date defaults if configured
    if query_config.get("use_current_date_default", False):
        parameters = apply_current_date_defaults(parameters)

    # Apply any parameter overrides (user-provided values take precedence)
    if param_overrides:
        parameters.update(param_overrides)

    pipeline_template = query_config.get("pipeline", [])
    pipeline = copy.deepcopy(pipeline_template)
    pipeline = replace_placeholders(pipeline, parameters)

    return pipeline


def flatten_document(doc: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """Flatten nested dictionary for Excel output."""
    items = []
    for k, v in doc.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict) and not any(key.startswith('$') for key in v.keys()):
            items.extend(flatten_document(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def format_cell_value(value: Any) -> Any:
    """Format a value for Excel cell."""
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')

    if isinstance(value, dict):
        if '$date' in value:
            try:
                date_val = value['$date']
                if isinstance(date_val, str):
                    dt = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(date_val, (int, float)):
                    dt = datetime.fromtimestamp(date_val / 1000)
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                return str(value)
        elif '$oid' in value:
            return value['$oid']
        else:
            return json.dumps(value, default=str)

    if isinstance(value, (int, float)) and abs(value) > 1000000:
        return str(int(value))

    if isinstance(value, list):
        return ', '.join(str(item) for item in value)

    return value


def create_mongodb_query_tool(session_id: str, session_folder: str):
    """
    Factory function to create a session-specific MongoDB query tool.

    Args:
        session_id: Unique session ID (ws_id)
        session_folder: Absolute path to session folder
    """

    # Initialize query executor (shared across tool calls)
    executor = MongoDBQueryExecutor()

    def generate_reports(
        query_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sme_id: Optional[int] = None,
        call_direction: Optional[str] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Generate reports by executing pre-configured MongoDB queries and exporting results to Excel.

        This tool runs READ-ONLY queries against MongoDB and exports results to Excel.
        Queries are defined in config/queries.json and can be customized via parameters.

        Args:
            query_name: Name of the report/query to generate (e.g., 'calling_cdr_incoming',
                       'calling_cdr_outgoing', 'agent_performance').
                       Use 'list' to see all available reports.
            start_date: Override start date (format: YYYY-MM-DDTHH:MM:SS).
                       If not provided, uses current date.
            end_date: Override end date (format: YYYY-MM-DDTHH:MM:SS).
                     If not provided, uses current date.
            sme_id: Override SME ID filter
            call_direction: Override call direction ('INCOMING' or 'OUTGOING')
            limit: Override result limit
            skip: Override skip count for pagination
            output_filename: Custom filename for Excel output (default: {query_name}_report.xlsx)

        Returns:
            Download URL for the Excel file with report data
        """
        try:
            logger.info(f"[{session_id}] Executing MongoDB query: {query_name}")

            # Load queries config
            queries = load_queries_config()

            # Handle list command
            if query_name.lower() == "list":
                query_list = []
                for name, config in queries.items():
                    desc = config.get("description", "No description")
                    collection = config.get("collection", "unknown")
                    params = list(config.get("parameters", {}).keys())
                    query_list.append(f"- **{name}**\n  Collection: {collection}\n  Description: {desc}\n  Parameters: {params}")
                return "Available queries:\n\n" + "\n\n".join(query_list)

            # Validate query name
            if query_name not in queries:
                available = ", ".join(queries.keys())
                return f"Error: Query '{query_name}' not found. Available queries: {available}"

            query_config = queries[query_name]

            # Build parameter overrides
            param_overrides = {}
            if start_date:
                param_overrides["start_date"] = start_date
            if end_date:
                param_overrides["end_date"] = end_date
            if sme_id is not None:
                param_overrides["sme_id"] = sme_id
            if call_direction:
                param_overrides["call_direction"] = call_direction
            if limit is not None:
                param_overrides["limit"] = limit
            if skip is not None:
                param_overrides["skip"] = skip

            # Get the actual dates that will be used (for reporting)
            effective_params = query_config.get("parameters", {}).copy()
            if query_config.get("use_current_date_default", False):
                effective_params = apply_current_date_defaults(effective_params)
            if param_overrides:
                effective_params.update(param_overrides)

            actual_start_date = effective_params.get("start_date", "N/A")
            actual_end_date = effective_params.get("end_date", "N/A")

            # Build pipeline with parameters
            collection_name = query_config.get("collection", "calling_cdr")
            pipeline = build_pipeline(query_config, param_overrides)

            logger.info(f"[{session_id}] Executing on collection: {collection_name}")
            logger.info(f"[{session_id}] Date range: {actual_start_date} to {actual_end_date}")

            # Execute query
            executor.connect()
            results = executor.execute_aggregation(collection_name, pipeline)

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

            # Collect headers from sample documents
            all_keys = set()
            for doc in results[:100]:
                flat_doc = flatten_document(doc)
                all_keys.update(flat_doc.keys())

            all_keys.discard('_id')
            headers = sorted(list(all_keys))

            # Write headers
            ws.append(headers)

            # Write data rows
            rows_written = 0
            for doc in results:
                flat_doc = flatten_document(doc)
                row = [format_cell_value(flat_doc.get(key)) for key in headers]
                ws.append(row)
                rows_written += 1

            wb.save(output_path)
            wb.close()

            logger.info(f"[{session_id}] Excel saved: {output_path} ({rows_written} rows)")

            # Prepare top 10 records summary for agent
            summary_records = []
            # Key fields for summary - supports both old field names and new aliased names
            key_fields = [
                'Date & Time', 'start_date_time',
                'Agent Name', 'agent_name',
                'Customer Number', 'customer_number',
                'Customer Name', 'customer_name',
                'Call Duration', 'duration',
                'Call Status', 'call_status',
                'Disconnected By', 'disconnected_by',
                'Session Id', 'session_id',
                'Campaign Name', 'campaign_name',
                'Queue Name', 'queue_name'
            ]

            for doc in results[:5]:
                flat_doc = flatten_document(doc)
                summary_record = {}
                for field in key_fields:
                    if field in flat_doc:
                        summary_record[field] = format_cell_value(flat_doc[field])
                # If key_fields not found, use first 8 available fields
                if not summary_record:
                    for key in list(flat_doc.keys())[:8]:
                        summary_record[key] = format_cell_value(flat_doc[key])
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
    return tool(generate_reports)
