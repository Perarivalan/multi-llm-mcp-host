import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server

from mcp.types import (
    CallToolRequestParams,
    ListToolsResult,
)

# Import all tools from modular packages
from tools import (
    health_tool,
    errors_tool,
    figma_files_tool,
    figma_components_tool,
    design_tokens_tool,
)

# Import tool handlers
from handlers import handle_tool_call


# -------------------------------------------------
# LIST TOOLS
# -------------------------------------------------

async def list_tools(
    ctx,
    params,
) -> ListToolsResult:

    return ListToolsResult(
        tools=[
            # Telemetry tools
            health_tool,
            errors_tool,
            # Figma/Design tools
            figma_files_tool,
            figma_components_tool,
            design_tokens_tool,
        ]
    )


# -------------------------------------------------
# CALL TOOL
# -------------------------------------------------

async def call_tool(
    ctx,
    params: CallToolRequestParams,
):
    """
    Route tool calls to the appropriate handler.
    This now delegates to the modular handlers.
    """
    return await handle_tool_call(params)


# -------------------------------------------------
# CREATE SERVER
# -------------------------------------------------

server = Server(
    "custom-application-server",
    on_list_tools=list_tools,
    on_call_tool=call_tool,
)


# -------------------------------------------------
# START SERVER
# -------------------------------------------------

async def main():

    async with stdio_server() as streams:

        await server.run(
            streams[0],
            streams[1],
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())