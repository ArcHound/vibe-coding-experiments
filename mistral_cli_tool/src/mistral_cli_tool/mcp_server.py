import requests
import logging

from typing import Annotated
from pydantic import Field

from fastmcp import FastMCP

from mistral_cli_tool import LOGGER_NAME

log = logging.getLogger(LOGGER_NAME)

MCP_SERVER_NAME = "MistralCLIServer"

mcp_server = FastMCP(name=MCP_SERVER_NAME)


@mcp_server.resource("greeting://{name}")
def get_greeting(name: Annotated[str, Field(description="Name to greet")]) -> str:
    """Get a greeting, yay."""
    return f"Hey {name}!"


@mcp_server.tool()
def simple_get(url: str) -> str:
    """Get URL"""
    return requests.get(url).text


@mcp_server.tool()
def weather(location: Annotated[str, Field(description="Location to get weather for")]):
    """Get weather for location"""
    return {"desc": "Raining", "temp": "18", "temp_unit": "C"}


if __name__ == "__main__":
    mcp_server.run()
