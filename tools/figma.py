"""
Figma Tools - Design system and component management
"""

from mcp.types import Tool


figma_files_tool = Tool(
    name="get_figma_files",
    description=(
        "Get list of Figma design files, their metadata, "
        "including status, last modified date, and contributors."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "Figma project ID to filter files. Leave empty for all files."
            },
            "filter": {
                "type": "string",
                "description": "Filter by file name or status (active, archived, etc)"
            }
        },
        "required": [],
    },
)


figma_components_tool = Tool(
    name="get_figma_components",
    description=(
        "Get design components from a Figma file, including "
        "component name, type, and usage count."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "file_id": {
                "type": "string",
                "description": "Figma file ID to fetch components from"
            },
            "component_type": {
                "type": "string",
                "description": "Filter by component type (e.g., button, input, card, modal, etc)"
            }
        },
        "required": ["file_id"],
    },
)


design_tokens_tool = Tool(
    name="get_design_tokens",
    description=(
        "Get design tokens (colors, spacing, typography, etc) "
        "from the design system."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "token_type": {
                "type": "string",
                "enum": ["colors", "spacing", "typography", "shadows", "all"],
                "description": "Type of design tokens to retrieve"
            },
            "category": {
                "type": "string",
                "description": "Filter by category (e.g., 'primary', 'secondary', 'neutral'). Leave empty for all."
            }
        },
        "required": ["token_type"],
    },
)
