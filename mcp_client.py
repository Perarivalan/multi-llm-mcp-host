import sys
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters


class MCPClient:

    def __init__(self):

        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["mcp_server.py"],
            cwd=Path(__file__).parent,
        )

        self.client = None


    async def connect(self):

        self.client = Client(
            self.server_params
        )

        await self.client.__aenter__()

        print("MCP Client connected.")


    async def disconnect(self):

        if self.client:

            await self.client.__aexit__(
                None,
                None,
                None,
            )


    async def list_tools(self):

        result = await self.client.list_tools()

        return result.tools


    async def call_tool(
        self,
        name,
        arguments,
    ):

        return await self.client.call_tool(
            name,
            arguments,
        )