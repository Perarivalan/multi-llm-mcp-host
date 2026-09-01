"""
Tool Handlers - Execute tool calls and return results
"""

import json
from mcp.types import CallToolRequestParams, CallToolResult, TextContent


# =====================================================
# TELEMETRY HANDLERS
# =====================================================

def handle_get_application_health(params: CallToolRequestParams) -> CallToolResult:
    """Handle get_application_health tool call."""
    
    all_data = {
        "status": "Degraded",
        "requests": 12500,
        "failed_requests": 430,
        "error_rate": 3.44,
        "average_response_time_ms": 850,
    }
    
    # Filter by included metrics if specified
    include_metrics = params.arguments.get("include_metrics", [])
    if include_metrics:
        data = {k: v for k, v in all_data.items() if k in include_metrics}
    else:
        data = all_data
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps(data, indent=2),
            )
        ]
    )


def handle_get_recent_errors(params: CallToolRequestParams) -> CallToolResult:
    """Handle get_recent_errors tool call."""
    
    all_errors = [
        {
            "type": "SqlException",
            "count": 120,
            "message": "SQL connection timeout",
        },
        {
            "type": "HttpRequestException",
            "count": 75,
            "message": "Payment service timeout",
        },
        {
            "type": "TimeoutException",
            "count": 45,
            "message": "API request timeout",
        },
    ]
    
    # Filter by error type if specified
    error_type = params.arguments.get("error_type", "")
    if error_type:
        filtered_errors = [e for e in all_errors if e["type"] == error_type]
    else:
        filtered_errors = all_errors
    
    # Apply limit if specified
    limit = params.arguments.get("limit")
    if limit:
        filtered_errors = filtered_errors[:limit]
    
    data = filtered_errors
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps(data, indent=2),
            )
        ]
    )


# =====================================================
# FIGMA HANDLERS
# =====================================================

def handle_get_figma_files(params: CallToolRequestParams) -> CallToolResult:
    """Handle get_figma_files tool call."""
    
    all_files = [
        {
            "id": "file_001",
            "name": "Design System - Components",
            "project_id": "proj_001",
            "status": "active",
            "last_modified": "2026-08-30",
            "contributors": 3,
        },
        {
            "id": "file_002",
            "name": "Web Application UI",
            "project_id": "proj_001",
            "status": "active",
            "last_modified": "2026-08-29",
            "contributors": 5,
        },
        {
            "id": "file_003",
            "name": "Mobile App Designs",
            "project_id": "proj_002",
            "status": "active",
            "last_modified": "2026-08-25",
            "contributors": 2,
        },
        {
            "id": "file_004",
            "name": "Error Page Redesign",
            "project_id": "proj_001",
            "status": "archived",
            "last_modified": "2026-08-20",
            "contributors": 1,
        },
    ]
    
    # Filter by project_id if specified
    project_id = params.arguments.get("project_id", "")
    if project_id:
        filtered_files = [f for f in all_files if f["project_id"] == project_id]
    else:
        filtered_files = all_files
    
    # Filter by name or status if specified
    filter_str = params.arguments.get("filter", "").lower()
    if filter_str:
        filtered_files = [
            f for f in filtered_files
            if filter_str in f["name"].lower() or filter_str == f["status"].lower()
        ]
    
    data = filtered_files
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps(data, indent=2),
            )
        ]
    )


def handle_get_figma_components(params: CallToolRequestParams) -> CallToolResult:
    """Handle get_figma_components tool call."""
    
    # Simulated components for file_001 (Design System)
    components_by_file = {
        "file_001": [
            {
                "name": "Button",
                "type": "button",
                "variants": ["primary", "secondary", "disabled"],
                "usage_count": 234,
            },
            {
                "name": "Input Field",
                "type": "input",
                "variants": ["text", "email", "password"],
                "usage_count": 189,
            },
            {
                "name": "Card",
                "type": "card",
                "variants": ["elevated", "outlined"],
                "usage_count": 156,
            },
            {
                "name": "Modal",
                "type": "modal",
                "variants": ["alert", "confirmation", "form"],
                "usage_count": 78,
            },
        ],
        "file_002": [
            {
                "name": "Header",
                "type": "layout",
                "variants": ["default", "sticky"],
                "usage_count": 12,
            },
            {
                "name": "Footer",
                "type": "layout",
                "variants": ["default"],
                "usage_count": 8,
            },
        ]
    }
    
    file_id = params.arguments.get("file_id", "")
    component_type = params.arguments.get("component_type", "").lower()
    
    # Get components for the file
    components = components_by_file.get(file_id, [])
    
    # Filter by component type if specified
    if component_type:
        components = [c for c in components if c["type"].lower() == component_type]
    
    data = components if components else {"message": f"No components found for file {file_id}"}
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps(data, indent=2),
            )
        ]
    )


def handle_get_design_tokens(params: CallToolRequestParams) -> CallToolResult:
    """Handle get_design_tokens tool call."""
    
    tokens_data = {
        "colors": {
            "primary": ["#007AFF", "#0051D5"],
            "secondary": ["#5AC8FA", "#34C759"],
            "neutral": ["#F2F2F7", "#8E8E93", "#000000"],
            "status": {
                "success": "#34C759",
                "warning": "#FF9500",
                "error": "#FF3B30",
            }
        },
        "spacing": {
            "xs": "4px",
            "sm": "8px",
            "md": "16px",
            "lg": "24px",
            "xl": "32px",
        },
        "typography": {
            "heading_1": {"size": "32px", "weight": "700", "line_height": "1.2"},
            "heading_2": {"size": "24px", "weight": "600", "line_height": "1.3"},
            "body": {"size": "16px", "weight": "400", "line_height": "1.5"},
            "caption": {"size": "12px", "weight": "400", "line_height": "1.4"},
        },
        "shadows": {
            "sm": "0 2px 4px rgba(0,0,0,0.1)",
            "md": "0 4px 12px rgba(0,0,0,0.15)",
            "lg": "0 8px 24px rgba(0,0,0,0.2)",
        }
    }
    
    token_type = params.arguments.get("token_type", "all")
    category = params.arguments.get("category", "").lower()
    
    # Get specific token type or all
    if token_type == "all":
        data = tokens_data
    else:
        data = tokens_data.get(token_type, {})
    
    # Filter by category if specified
    if category and isinstance(data, dict):
        if category in data:
            data = {category: data[category]}
        else:
            data = {"message": f"Category '{category}' not found"}
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps(data, indent=2),
            )
        ]
    )


# =====================================================
# TOOL DISPATCHER
# =====================================================

TOOL_HANDLERS = {
    # Telemetry tools
    "get_application_health": handle_get_application_health,
    "get_recent_errors": handle_get_recent_errors,
    # Figma tools
    "get_figma_files": handle_get_figma_files,
    "get_figma_components": handle_get_figma_components,
    "get_design_tokens": handle_get_design_tokens,
}


async def handle_tool_call(
    params: CallToolRequestParams,
) -> CallToolResult:
    """
    Dispatch tool calls to appropriate handlers.
    
    Args:
        params: Call tool request parameters
        
    Returns:
        Tool call result
    """
    handler = TOOL_HANDLERS.get(params.name)
    
    if not handler:
        return CallToolResult(
            is_error=True,
            content=[
                TextContent(
                    type="text",
                    text=f"Unknown tool: {params.name}",
                )
            ],
        )
    
    try:
        return handler(params)
    except Exception as e:
        return CallToolResult(
            is_error=True,
            content=[
                TextContent(
                    type="text",
                    text=f"Error executing tool {params.name}: {str(e)}",
                )
            ],
        )
