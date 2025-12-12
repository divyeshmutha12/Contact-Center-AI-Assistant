
"""
Excel Converter Tool for Data Extraction Agent

This tool converts EJSON data to Excel format using streaming write mode
for memory efficiency with large datasets.

Output format:
- Tool returns: [DOWNLOAD:outputs/filename.xlsx]
- WebSocket handler transforms to full URL with session path
- This allows deployment-agnostic file generation
"""

import os
import json
import logging
from datetime import datetime
from langchain.tools import tool
from openpyxl import Workbook
from bson import json_util

logger = logging.getLogger(__name__)


def _flatten_document(doc: dict, parent_key: str = '', sep: str = '_') -> dict:
    """
    Flatten nested dictionary for Excel output.
    Example: {"a": {"b": 1}} -> {"a_b": 1}
    """
    items = []
    for k, v in doc.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict) and not any(key.startswith('$') for key in v.keys()):
            items.extend(_flatten_document(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def _format_value(value):
    """
    Format a value for Excel cell.
    Handles dates, ObjectIds, and other BSON types.
    """
    if value is None:
        return ""

    # Handle MongoDB $date format
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
            return str(value)

    # Handle large numbers (prevent scientific notation)
    if isinstance(value, (int, float)) and abs(value) > 1000000:
        return str(int(value))

    # Handle lists
    if isinstance(value, list):
        return ', '.join(str(item) for item in value)

    return value


def create_excel_converter_tool(session_id: str, session_folder: str):
    """
    Factory function to create a session-specific Excel converter tool.

    Args:
        session_id: Unique session ID (ws_id)
        session_folder: Absolute path to session folder
    """

    def _read_ejson_from_file(file_path: str) -> list:
        """Read EJSON from a file path (for evicted large results)."""
        # Remove leading slash if present
        clean_path = file_path.lstrip('/')

        # Replace forward slashes with OS-appropriate separators
        clean_path = clean_path.replace('/', os.sep)

        # Join with session folder
        actual_path = os.path.join(session_folder, clean_path)

        # Normalize path to fix any remaining separator issues
        actual_path = os.path.normpath(actual_path)

        # Add .json extension if not present
        if not actual_path.endswith('.json'):
            actual_path = actual_path + '.json'

        logger.info(f"Reading EJSON from: {actual_path}")

        with open(actual_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return json_util.loads(content)

    def _parse_ejson(source: str) -> list:
        """Parse EJSON from either a file path or raw content."""
        if source.startswith('/'):
            return _read_ejson_from_file(source)
        else:
            return json_util.loads(source)

    def convert_to_excel(source: str, output_filename: str, sheet_name: str = "Report") -> str:
        """
        Convert EJSON data to Excel file for user download.

        Use this tool when the user requests a report or data export. It handles:
        - File paths (e.g., /large_tool_results/xxx.json) for auto-evicted large results
        - Raw EJSON strings for smaller results

        Args:
            source: Either a file path starting with '/' (for evicted large results)
                    OR raw EJSON string (for small results)
            output_filename: Name for the output file (e.g., "incoming_calls_report.xlsx")
            sheet_name: Name for the Excel worksheet (default: "Report")

        Returns:
            Download URL for the Excel file
        """
        try:
            logger.info(f"[{session_id}] Converting EJSON to Excel: output={output_filename}")

            # DEBUG: Log source details
            logger.info(f"[{session_id}] Source type: {'file_path' if source.startswith('/') else 'inline_ejson'}")
            logger.info(f"[{session_id}] Source length: {len(source)} characters")
            if not source.startswith('/'):
                logger.info(f"[{session_id}] Source preview (first 200 chars): {source[:200]}")
                logger.info(f"[{session_id}] Source preview (last 200 chars): {source[-200:]}")

            # Parse the EJSON data
            documents = _parse_ejson(source)

            if not documents:
                return "Error: No data to convert. The source contains no documents."

            if not isinstance(documents, list):
                documents = [documents]

            logger.info(f"[{session_id}] Parsed {len(documents)} documents")

            # Ensure filename has .xlsx extension
            if not output_filename.endswith('.xlsx'):
                output_filename = f"{output_filename}.xlsx"

            # Create output path in session folder
            output_dir = os.path.join(session_folder, "outputs")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)

            # Use write_only mode for memory efficiency
            wb = Workbook(write_only=True)
            ws = wb.create_sheet(title=sheet_name)

            # Collect all unique keys for headers
            all_keys = set()
            sample_docs = documents[:100]
            for doc in sample_docs:
                flat_doc = _flatten_document(doc)
                all_keys.update(flat_doc.keys())

            # Remove _id from headers
            all_keys.discard('_id')
            headers = sorted(list(all_keys))

            # Write headers
            ws.append(headers)

            # Write data rows (streaming)
            rows_written = 0
            for doc in documents:
                flat_doc = _flatten_document(doc)
                row = [_format_value(flat_doc.get(key)) for key in headers]
                ws.append(row)
                rows_written += 1

            # Save the workbook
            wb.save(output_path)
            wb.close()

            logger.info(f"[{session_id}] Excel saved: {output_path} ({rows_written} rows)")

            # Return relative path only - WebSocket layer adds session prefix and constructs URL
            # Format: [DOWNLOAD:relative_path] - will be transformed by websocket handler
            relative_path = f"outputs/{output_filename}"

            return f"Excel report created with {rows_written} records.\n\n[DOWNLOAD:{relative_path}]"

        except FileNotFoundError as e:
            logger.error(f"[{session_id}] File not found: {e}")
            return f"Error: Could not find the source file. {str(e)}"
        except json.JSONDecodeError as e:
            logger.error(f"[{session_id}] JSON parse error: {e}")
            # Log context around the error position for debugging
            if hasattr(e, 'pos') and e.pos and not source.startswith('/'):
                start = max(0, e.pos - 150)
                end = min(len(source), e.pos + 150)
                logger.error(f"[{session_id}] Error at position {e.pos}")
                logger.error(f"[{session_id}] Context: ...{source[start:end]}...")
            return f"Error: Invalid EJSON format. {str(e)}"
        except Exception as e:
            logger.error(f"[{session_id}] Excel conversion error: {e}")
            return f"Error converting to Excel: {str(e)}"

    # Return decorated tool
    return tool(convert_to_excel)
