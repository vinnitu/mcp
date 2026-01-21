from fastmcp import FastMCP
mcp = FastMCP("my-tools")

@mcp.tool()
def get_telegram_message_content_by_ling(url: str) -> str:
    return "Not implemented yet"
