#!/usr/bin/env python3

import os
import json
import csv
import logging
import sys
import time
import math
from functools import update_wrapper
import cProfile
import pstats

import asyncio
from asyncio import Queue

import click
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

from mistral_cli_tool.ai_client import AIClient

from mistralai import Mistral
from mistralai.models.assistantmessage import AssistantMessage
from mistralai.models.function import Function
from mistralai.models.toolmessage import ToolMessage
from mistralai.models.usermessage import UserMessage

load_dotenv()

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

from mistral_cli_tool import LOGGER_NAME

log = logging.getLogger(LOGGER_NAME)


log_levels = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

api_key = os.environ["MISTRAL_AI_KEY"]

client = Mistral(api_key=api_key)

server_params = StdioServerParameters(
    command="python",  # Executable
    args=["mcp_server.py"],  # Optional command line arguments
    env=None,  # Optional environment variables
)


def log_decorator(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        log.setLevel(log_levels[ctx.params["log_level"]])
        log.info("Starting")
        r = ctx.invoke(f, *args, **kwargs)
        log.info("Finishing")
        return r

    return update_wrapper(new_func, f)


def time_decorator(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        t1 = time.perf_counter()
        try:
            r = ctx.invoke(f, *args, **kwargs)
            return r
        except Exception as e:
            raise e
        finally:
            t2 = time.perf_counter()
            mins = math.floor(t2 - t1) // 60
            hours = mins // 60
            secs = (t2 - t1) - 60 * mins - 3600 * hours
            log.info(f"Execution in {hours:02d}:{mins:02d}:{secs:0.4f}")

    return update_wrapper(new_func, f)


@click.command()
@click.argument("prompt", nargs=-1)
@click.option(
    "--model",
    help="Model to use",
    default="mistral-large-latest",
    show_default=True,
)
@click.option(
    "--api-key",
    help="Mistral API key",
    envvar="MISTRAL_AI_KEY",
)
@click.option(
    "--input-file",
    help="Input file [default: STDIN]",
    type=click.Path(readable=True, file_okay=True, dir_okay=False),
    default="-",
)
@click.option(
    "--log-level",
    default="WARNING",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    show_default=True,
    help="Set logging level.",
    envvar="LOG_LEVEL",
)
@log_decorator
@time_decorator
def main(prompt, model, api_key, input_file, log_level):
    """Console script for hey_ai."""
    # ======================================================================
    #                        Your script starts here!
    # ======================================================================
    one_pass = False
    if input_file == "-" and sys.stdin.isatty() and len(prompt) > 0:
        one_pass = True
        in_data = " ".join(prompt)
    elif input_file != "-":
        one_pass = True
        with click.open_file(input_file, "r") as f:
            in_data = f.read()
    else:
        in_data = ""

    input_queue = Queue()
    output_queue = Queue()

    client = AIClient(api_key, model, input_queue, output_queue)
    asyncio.run(run_it(client, input_queue, output_queue, in_data, one_pass))
    return 0


async def run_it(client, input_queue, output_queue, in_data, one_pass):
    await client.start_loop()
    if one_pass:
        await input_queue.put(in_data)
        await input_queue.put(None)
        output_msg = await output_queue.get()
        click.secho(output_msg, fg="green")
        output_queue.task_done()
        output_fin = await output_queue.get()
        output_queue.task_done()
        await input_queue.join()
        await output_queue.join()
        if output_fin is not None:
            raise ValueError("WTF did you do :(")
    else:
        click.echo("Interactive mode: exit with 'EXIT'")
        while True:
            message = click.prompt(">", type=str)
            log.info(message)
            if message == "EXIT":
                await input_queue.put(None)
            else:
                await input_queue.put(message)
            log.info("message sent")
            reply = await output_queue.get()
            log.info(reply)
            if reply is None:
                output_queue.task_done()
                break
            click.secho(reply, fg="green")
            output_queue.task_done()
    log.debug("before end_loop")
    await client.end_loop()


if __name__ == "__main__":
    main()
