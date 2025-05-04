import requests
import logging
import os

from typing import Annotated
from pydantic import Field
from datetime import datetime

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


WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")


@mcp_server.tool()
def weather(
    location: Annotated[
        str,
        Field(
            description="City (London) or ZIP (10001) or IATA (DXB) or coordinates (48.8567,2.3508) to get current weather for"
        ),
    ],
):
    """Get current weather for location specified by City (London) or ZIP (10001) or IATA (DXB) or coordinates (48.8567,2.3508)"""
    if not WEATHER_API_KEY:
        return "No weather API key provided"
    return (
        requests.get(
            f"https://api.weatherapi.com/v1/current.json?q={location}&key={WEATHER_API_KEY}"
        )
        .json()
        .get("current", {})
    )


@mcp_server.tool()
def time():
    return datetime.now().strftime("%a %d %b %Y, %I:%M%p")


if __name__ == "__main__":
    mcp_server.run(transport="sse")
