import os
import click
import requests

# Base URL for the Mistral AI API (you need to replace this with the actual API endpoint)
API_BASE_URL = "https://api.mistralai.com/v1/generate"

def get_api_key():
    """Retrieve the API key from the environment variable."""
    api_key = os.getenv("MISTRAL_AI_KEY")
    if not api_key:
        raise ValueError("MISTRAL_AI_KEY environment variable not set")
    return api_key

@click.command()
@click.option('--prompt', required=True, help='The input prompt for Mistral AI.')
def call_mistral_ai(prompt):
    """Call the Mistral AI API with the given prompt."""
    api_key = get_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt
    }

    response = requests.post(API_BASE_URL, headers=headers, json=payload)

    if response.status_code == 200:
        click.echo("Response from Mistral AI:")
        click.echo(response.json().get('choices')[0].get('text'))
    else:
        click.echo(f"Failed to call Mistral AI API. Status code: {response.status_code}")
        click.echo(response.text)

if __name__ == '__main__':
    call_mistral_ai()

