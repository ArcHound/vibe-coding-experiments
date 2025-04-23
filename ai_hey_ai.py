#!/usr/bin/env python3

import os
import click
import requests
import json


@click.command()
@click.argument("prompt", nargs=-1)
@click.option(
    "--model", default="mistral-small-latest", help="The model to use for the AI call."
)
def call_mistral_ai(prompt, model):
    """Call the Mistral AI API with the given prompt."""
    api_key = os.getenv("MISTRAL_AI_KEY")
    if not api_key:
        raise click.ClickException("MISTRAL_AI_KEY environment variable not set")

    # Join the prompt list into a single string
    prompt = " ".join(prompt)

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        # Add any other parameters required by the API here
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_json = response.json()
        # Adjust the following line based on the actual structure of the API response
        click.echo(response_json["choices"][0]["message"]["content"])
    else:
        raise click.ClickException(f"Error: {response.status_code} - {response.text}")


if __name__ == "__main__":
    call_mistral_ai()
