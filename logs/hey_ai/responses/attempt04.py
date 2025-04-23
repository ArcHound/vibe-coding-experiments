import os
import requests
import click


@click.command()
@click.argument("prompt", required=True)
def call_mistral_ai(prompt):
    # Get the API key from the environment variable
    api_key = os.getenv("MISTRAL_AI_KEY")
    if not api_key:
        click.echo("Error: MISTRAL_AI_KEY environment variable is not set.")
        return

    # Define the API URL
    url = "https://api.mistral.ai/v1/generate"

    # Define the headers with the API key
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Define the payload with the prompt
    payload = {"prompt": prompt}

    # Make the API request
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        click.echo(response.json().get("response", "No response received."))
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: {e}")


if __name__ == "__main__":
    call_mistral_ai()
