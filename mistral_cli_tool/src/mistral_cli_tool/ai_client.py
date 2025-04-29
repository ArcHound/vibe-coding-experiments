#!/usr/bin/env python3

import os
import json
import csv
import logging
import sys
import time
import math

from mistralai import Mistral
from mistralai.models.assistantmessage import AssistantMessage
from mistralai.models.function import Function
from mistralai.models.toolmessage import ToolMessage
from mistralai.models.usermessage import UserMessage

from fastmcp import Client
from mistral_cli_tool.mcp_server import mcp_server
from mistral_cli_tool import LOGGER_NAME

import asyncio
from asyncio import Queue

log = logging.getLogger(LOGGER_NAME)


class AIClient:
    def __init__(
        self,
        api_key,
        model,
        input_queue: Queue,
        output_queue: Queue,
        mcp_server=mcp_server,
    ):
        self.client = Mistral(api_key=api_key)
        self.model = model
        self.mcp_server = mcp_server
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.messages = list()
        asyncio.run(self.get_mcp_definitions())

    async def get_mcp_definitions(self):
        async with Client(self.mcp_server) as client:
            # List available resources
            self.resources = await client.list_resources()
            log.info(self.resources)

            # List available tools
            self.mcp_tools = await client.list_tools()
            self.tools = [tool_mcp_to_mistral(tool) for tool in self.mcp_tools]
            log.info(self.tools)

    def add_mcp(self, mcp_server):
        self.mcp_server = mcp_server
        pass

    async def start_loop(self):
        self.worker_task = asyncio.create_task(self.worker())

    async def end_loop(self):
        await self.input_queue.join()
        await self.output_queue.join()
        self.worker_task.cancel()
        try:
            await self.worker_task
        except asyncio.CancelledError:
            pass

    async def worker(self):
        log.info("worker start")
        while True:
            user_query = await self.input_queue.get()
            if user_query is None:
                self.input_queue.task_done()
                await self.output_queue.put(None)
                break
            result = await self.single_pass(user_query)
            self.input_queue.task_done()
        log.info("worker end")

    async def single_pass(self, user_query):
        self.messages.append(UserMessage(content=user_query, tools=self.tools))
        time.sleep(1)
        chat_response = self.client.chat.complete(
            model=self.model,
            messages=self.messages,
            tools=self.tools,
            parallel_tool_calls=False,
        )
        log.info(chat_response)
        tool_calls = chat_response.choices[0].message.tool_calls
        if tool_calls is not None:
            self.messages.append(
                AssistantMessage(
                    content=chat_response.choices[0].message.content,
                    tool_calls=chat_response.choices[0].message.tool_calls,
                )
            )
            async with Client(self.mcp_server) as mcp_client:
                for tool_call in chat_response.choices[0].message.tool_calls:
                    log.info(tool_call)
                    function_name = tool_call.function.name
                    function_params = json.loads(tool_call.function.arguments)
                    function_response = await mcp_client.call_tool(
                        function_name, arguments=function_params
                    )
                    log.info(function_response)
                    self.messages.append(
                        ToolMessage(
                            name=function_name,
                            content=function_response[0].text,
                            tool_call_id=tool_call.id,
                        )
                    )
            time.sleep(1)
            chat_response = self.client.chat.complete(
                model=self.model,
                messages=self.messages,
                tools=self.tools,
            )
            self.messages.append(
                AssistantMessage(
                    content=chat_response.choices[0].message.content,
                    tool_calls=chat_response.choices[0].message.tool_calls,
                )
            )
        await self.output_queue.put(chat_response.choices[0].message.content)


def tool_mcp_to_mistral(tool):
    json_tool = vars(tool)
    mistral_tool = dict()
    mistral_tool["name"] = json_tool["name"]
    mistral_tool["description"] = json_tool["description"]
    mistral_tool["parameters"] = dict()
    mistral_tool["parameters"]["properties"] = json_tool["inputSchema"]["properties"]
    mistral_tool["parameters"]["required"] = json_tool["inputSchema"]["required"]
    return {"type": "function", "function": mistral_tool}


if __name__ == "__main__":
    client = AIClient(
        api_key=os.environ.get("MISTRAL_AI_KEY"), model="mistral-large-latest"
    )
    log.info(mcp_server)
    # log.info(json.dumps(client.tools, indent=2))
    # client.start_loop("What's the weather in Olomouc")
