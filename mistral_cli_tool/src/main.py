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

import click
from dotenv import load_dotenv

from mistralai import Mistral

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)


log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
}

api_key = os.environ["MISTRAL_AI_KEY"]
model = "codestral-latest"

client = Mistral(api_key=api_key)

def log_decorator(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        log.setLevel(log_levels[ctx.params["log_level"]])
        log.info("Starting")
        r =  ctx.invoke(f,  *args, **kwargs)
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
            mins = math.floor(t2-t1) // 60
            hours = mins // 60
            secs = (t2-t1) - 60 * mins - 3600 * hours
            log.info(f"Execution in {hours:02d}:{mins:02d}:{secs:0.4f}")
        
    return update_wrapper(new_func, f)


@click.command()
@click.argument('prompt', nargs=-1)
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
    envvar="LOG_LEVEL"
)
@log_decorator
@time_decorator
def main(
        prompt,
        input_file,
        log_level):
    """Console script for hey_ai."""
    # ======================================================================
    #                        Your script starts here!
    # ======================================================================
    if input_file == "-" and sys.stdin.isatty():
        in_data = " ".join(prompt)
    else: 
        with click.open_file(input_file, "r") as f:
            in_data = f.read()
    chat_response = client.chat.complete(
        model= model,
        messages = [
            {
                "role": "user",
                "content": f"{in_data}",
            },
        ]
    )
    click.echo(chat_response.choices[0].message.content)
    return 0


if __name__ == "__main__":
    main()
