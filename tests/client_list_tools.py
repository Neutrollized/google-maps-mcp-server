import asyncio
from fastmcp import Client


async def test_server_tools():
    # fastmcp run server.py --transport streamable-http
    # use "/sse" for sse transport
    async with Client("http://localhost:8000/mcp") as client:
        tools = await client.list_tools()

        for tool in tools:
            print(f"[Tool found]: {tool.name}")


if __name__ == "__main__":
    asyncio.run(test_server_tools())
