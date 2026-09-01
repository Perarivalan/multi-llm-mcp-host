"""
Telemetry Tools - Application health and monitoring
"""

from mcp.types import Tool


health_tool = Tool(
    name="get_application_health",
    description=(
        "Returns application health information "
        "including requests, failures, error rate "
        "and response time."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "include_metrics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific metrics to include: status, requests, failed_requests, error_rate, response_time. Leave empty for all."
            }
        },
        "required": [],
    },
)


errors_tool = Tool(
    name="get_recent_errors",
    description=(
        "Returns recent application errors "
        "including error type, count and message."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "error_type": {
                "type": "string",
                "description": "Filter errors by type (e.g., SqlException, HttpRequestException). Leave empty for all."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of errors to return (default: all)"
            }
        },
        "required": [],
    },
)
