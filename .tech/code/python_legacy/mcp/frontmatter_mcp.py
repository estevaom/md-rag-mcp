#!/usr/bin/env python3
import sys
import json
import os
import traceback
import re
import yaml
from datetime import datetime

# --- Early Startup Logging ---
print("[Frontmatter MCP Debug] Script starting up", file=sys.stderr, flush=True)
print(f"[Frontmatter MCP Debug] Python version: {sys.version}", file=sys.stderr, flush=True)
print(f"[Frontmatter MCP Debug] Current working directory: {os.getcwd()}", file=sys.stderr, flush=True)

# --- Configuration ---
# Calculate PROJECT_ROOT based on this script's location (.tech/code/mcp/frontmatter_mcp.py)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TECH_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # .tech/
PROJECT_ROOT = os.path.dirname(TECH_DIR)  # Project root directory

# --- Logging ---
def log_error(message):
    """Logs an error message to stderr."""
    print(f"[Frontmatter MCP Error] {message}", file=sys.stderr, flush=True)

def log_info(message):
    """Logs an info message to stderr."""
    print(f"[Frontmatter MCP Info] {message}", file=sys.stderr, flush=True)

# --- Frontmatter Query Functions ---
def extract_frontmatter_from_file(file_path):
    """Extract YAML frontmatter from a markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Match frontmatter between --- markers
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if match:
            try:
                return yaml.safe_load(match.group(1))
            except yaml.YAMLError:
                return None
    except Exception:
        return None
    return None

def find_journal_files_for_frontmatter(base_dir, start_date=None, end_date=None):
    """Find all journal markdown files, optionally filtered by date range."""
    files = []
    
    for root, dirs, filenames in os.walk(base_dir):
        for filename in filenames:
            if filename.endswith('.md'):
                file_path = os.path.join(root, filename)
                frontmatter_data = extract_frontmatter_from_file(file_path)
                
                if frontmatter_data and 'date' in frontmatter_data:
                    file_date = frontmatter_data['date']
                    
                    # Convert date to datetime if it's a string
                    if isinstance(file_date, str):
                        try:
                            file_date = datetime.strptime(file_date, '%Y-%m-%d').date()
                        except ValueError:
                            continue
                    elif isinstance(file_date, datetime):
                        file_date = file_date.date()
                    
                    # Filter by date range if provided
                    if start_date and file_date < start_date:
                        continue
                    if end_date and file_date > end_date:
                        continue
                    
                    files.append({
                        'file': file_path,
                        'date': file_date,
                        'frontmatter': frontmatter_data
                    })
    
    return sorted(files, key=lambda x: x['date'])

def query_frontmatter_fields(files, fields):
    """Extract specific fields from frontmatter data."""
    results = []
    
    for file_info in files:
        row = {
            'date': file_info['date'].isoformat(),
            'file': file_info['file']
        }
        
        for field in fields:
            value = file_info['frontmatter'].get(field)
            # Clean up values (remove comments, etc.)
            if isinstance(value, str) and '#' in value:
                value = value.split('#')[0].strip()
            row[field] = value
        
        results.append(row)
    
    return results

def calculate_frontmatter_stats(results, field):
    """Calculate basic statistics for a numeric field."""
    values = []
    skipped_values = []
    
    for row in results:
        val = row.get(field)
        if val is not None:
            try:
                # Handle range values like "3-4"
                if isinstance(val, str) and '-' in val:
                    # Try to parse as range (e.g., "3-4")
                    range_parts = val.split('-')
                    if len(range_parts) == 2:
                        try:
                            min_val = float(range_parts[0].strip())
                            max_val = float(range_parts[1].strip())
                            # Use midpoint of range
                            values.append((min_val + max_val) / 2)
                            continue
                        except ValueError:
                            pass
                
                # Try direct numeric conversion
                values.append(float(val))
            except (ValueError, TypeError):
                skipped_values.append(val)
    
    if not values:
        return None
    
    stats = {
        'count': len(values),
        'min': min(values),
        'max': max(values),
        'avg': sum(values) / len(values),
        'values': values
    }
    
    # Add info about skipped values if any
    if skipped_values:
        stats['skipped_values'] = skipped_values
        stats['skipped_count'] = len(skipped_values)
    
    return stats

def perform_frontmatter_query(fields=None, start_date=None, end_date=None, 
                             calculate_stats=False, output_format="json"):
    """
    Query frontmatter data from journal files.
    
    Args:
        fields (list): List of frontmatter fields to extract
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format  
        calculate_stats (bool): Whether to calculate statistics
        output_format (str): Output format (json, csv, table)
    
    Returns:
        tuple: (success, results_dict) where results_dict contains:
               - 'data': list of records
               - 'stats': statistics if requested
    """
    try:
        # Default fields if none provided
        if fields is None:
            fields = ['mood', 'anxiety', 'weight_kg']
        
        # Parse dates
        parsed_start_date = None
        parsed_end_date = None
        if start_date:
            try:
                parsed_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                return False, {"error": f"Invalid start_date format: {start_date}. Use YYYY-MM-DD."}
        if end_date:
            try:
                parsed_end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return False, {"error": f"Invalid end_date format: {end_date}. Use YYYY-MM-DD."}
        
        # Define journal directory
        journal_dir = os.path.join(PROJECT_ROOT, "journal")
        
        # Find and process files
        log_info(f"Querying frontmatter fields {fields} from {journal_dir}")
        files = find_journal_files_for_frontmatter(journal_dir, parsed_start_date, parsed_end_date)
        results = query_frontmatter_fields(files, fields)
        
        # Prepare response
        response_data = {
            'data': results,
            'fields_queried': fields,
            'files_processed': len(files),
            'records_found': len(results)
        }
        
        # Add date range info if provided
        if start_date or end_date:
            response_data['date_range'] = {
                'start_date': start_date,
                'end_date': end_date
            }
        
        # Calculate statistics if requested
        if calculate_stats:
            stats = {}
            for field in fields:
                field_stats = calculate_frontmatter_stats(results, field)
                if field_stats:
                    stats[field] = field_stats
            response_data['stats'] = stats
        
        # Format output based on requested format
        if output_format == 'csv':
            if results:
                headers = ['date', 'file'] + fields
                csv_lines = [','.join(headers)]
                for row in results:
                    values = [str(row.get(h, '')) for h in headers]
                    csv_lines.append(','.join(values))
                response_data['csv_output'] = '\n'.join(csv_lines)
        elif output_format == 'table':
            if results:
                headers = ['date'] + fields
                table_lines = []
                for row in results:
                    values = [str(row.get(h, '')) for h in headers]
                    table_lines.append('\t'.join(values))
                response_data['table_output'] = '\n'.join(table_lines)
        
        log_info(f"Frontmatter query completed: {len(results)} records from {len(files)} files")
        return True, response_data
        
    except Exception as e:
        log_error(f"Error in frontmatter query: {e}")
        log_error(traceback.format_exc())
        return False, {"error": f"Frontmatter query failed: {str(e)}"}

# --- MCP Response Formatting ---
def create_mcp_response(request_id, result=None, error=None):
    """Creates a JSON-RPC 2.0 response dictionary."""
    response = {"jsonrpc": "2.0", "id": request_id}
    if error:
        response["error"] = error
    else:
        response["result"] = result
    return response

def create_mcp_error(code, message):
    """Creates an MCP error object."""
    return {"code": code, "message": message}

# --- Main Server Loop ---
def main():
    """Reads MCP requests from stdin, processes them, writes responses to stdout."""
    log_info("Frontmatter MCP server started. Waiting for requests on stdin...")

    for line in sys.stdin:
        request_id = None
        try:
            log_info(f"Received request line: {line.strip()}")
            request = json.loads(line)
            request_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})
            log_info(f"Processing method: {method} for request ID: {request_id}")

            response = None

            if method == "initialize":
                log_info("Handling 'initialize' method.")
                response = create_mcp_response(request_id, result={
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "frontmatter-mcp-server",
                        "displayName": "Frontmatter Query Server",
                        "version": "0.1.0",
                    },
                    "capabilities": {
                        "tools": {
                            "listChanged": False
                        }
                    }
                })
            elif method == "notifications/initialized":
                log_info("Received initialized notification")
                response = None  # No response needed for notifications
                
            elif method == "tools/list":
                log_info("Handling 'tools/list' method.")
                response = create_mcp_response(request_id, result={
                    "tools": [
                        {
                            "name": "query_frontmatter",
                            "description": "Query and analyze frontmatter data from journal entries with optional statistics",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "fields": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Frontmatter fields to extract (default: ['mood', 'anxiety', 'weight_kg'])",
                                        "default": ["mood", "anxiety", "weight_kg"]
                                    },
                                    "start_date": {
                                        "type": "string",
                                        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                                        "description": "Start date filter (YYYY-MM-DD format)"
                                    },
                                    "end_date": {
                                        "type": "string", 
                                        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                                        "description": "End date filter (YYYY-MM-DD format)"
                                    },
                                    "stats": {
                                        "type": "boolean",
                                        "description": "Calculate statistics for numeric fields (default: false)",
                                        "default": False
                                    },
                                    "format": {
                                        "type": "string",
                                        "enum": ["json", "csv", "table"],
                                        "description": "Output format (default: json)",
                                        "default": "json"
                                    }
                                }
                            }
                        }
                    ]
                })

            elif method == "resources/list":
                log_info("Handling 'resources/list' method.")
                response = create_mcp_response(request_id, result={
                    "resources": []
                })
                
            elif method == "resources/templates/list":
                log_info("Handling 'resources/templates/list' method.")
                response = create_mcp_response(request_id, result={
                    "templates": []
                })
                
            elif method == "tools/call":
                log_info("Handling 'tools/call' method.")
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                log_info(f"Tool name: {tool_name}, Arguments: {arguments}")

                if tool_name == "query_frontmatter":
                    fields = arguments.get("fields", ["mood", "anxiety", "weight_kg"])
                    start_date = arguments.get("start_date")
                    end_date = arguments.get("end_date") 
                    stats = arguments.get("stats", False)
                    format_type = arguments.get("format", "json")
                    
                    log_info(f"Frontmatter query: fields={fields}, start_date={start_date}, end_date={end_date}, stats={stats}, format={format_type}")
                    
                    # Validate parameters
                    if not isinstance(fields, list) or not all(isinstance(f, str) for f in fields):
                        response = create_mcp_response(request_id, error=create_mcp_error(-32602, "Invalid params: 'fields' must be a list of strings."))
                    elif start_date and not isinstance(start_date, str):
                        response = create_mcp_response(request_id, error=create_mcp_error(-32602, "Invalid params: 'start_date' must be a string in YYYY-MM-DD format."))
                    elif end_date and not isinstance(end_date, str):
                        response = create_mcp_response(request_id, error=create_mcp_error(-32602, "Invalid params: 'end_date' must be a string in YYYY-MM-DD format."))
                    elif not isinstance(stats, bool):
                        response = create_mcp_response(request_id, error=create_mcp_error(-32602, "Invalid params: 'stats' must be a boolean."))
                    elif format_type not in ["json", "csv", "table"]:
                        response = create_mcp_response(request_id, error=create_mcp_error(-32602, "Invalid params: 'format' must be one of: json, csv, table."))
                    else:
                        # Execute frontmatter query
                        success, result_data = perform_frontmatter_query(
                            fields=fields,
                            start_date=start_date,
                            end_date=end_date,
                            calculate_stats=stats,
                            output_format=format_type
                        )
                        
                        if success:
                            # Format response for MCP
                            response_text = json.dumps(result_data, indent=2)
                            response = create_mcp_response(request_id, result={
                                "content": [{
                                    "type": "text",
                                    "text": response_text
                                }]
                            })
                        else:
                            # Handle error
                            error_msg = result_data.get('error', 'Unknown error in frontmatter query')
                            response = create_mcp_response(
                                request_id, 
                                error=create_mcp_error(-32000, f"Frontmatter query failed: {error_msg}")
                            )
                else:
                    log_error(f"Unknown tool called: {tool_name}")
                    response = create_mcp_response(request_id, error=create_mcp_error(-32601, f"Method not found: Unknown tool '{tool_name}'"))

            else:
                 log_error(f"Unknown method received: {method}")
                 response = create_mcp_response(request_id, error=create_mcp_error(-32601, f"Method not found: Unknown method '{method}'"))

            if response:
                response_json = json.dumps(response)
                log_info(f"Prepared response for ID {request_id}: {response_json[:200]}...")
                print(response_json, flush=True)
                log_info(f"Successfully sent response for request ID: {request_id}")
            elif method == "notifications/initialized":
                log_info(f"No response needed for notification: {method}")
            else:
                log_error(f"No response generated for request ID: {request_id}, method: {method}")

        except json.JSONDecodeError:
            log_error(f"JSONDecodeError: Failed to decode JSON request: {line.strip()}")
            error_response = create_mcp_response(request_id, error=create_mcp_error(-32700, "Parse error: Invalid JSON received."))
            print(json.dumps(error_response), flush=True)
        except Exception as e:
            log_error(f"Unexpected error processing request: {e}")
            log_error(traceback.format_exc())
            error_response = create_mcp_response(request_id, error=create_mcp_error(-32000, f"Internal server error: {e}"))
            print(json.dumps(error_response), flush=True)

# --- Script Execution Guard ---
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_info("Frontmatter MCP server stopped by KeyboardInterrupt.")
    except Exception as e:
        log_error(f"Unhandled exception in main execution: {e}")
        log_error(traceback.format_exc())
        sys.exit(1)
    finally:
        log_info("Frontmatter MCP server process ending.")
        