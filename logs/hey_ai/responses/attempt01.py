import click
import requests


@click.command()
@click.argument("prompt", required=True)
def call_mistral_ai(prompt):
    """
    Call the Mistral AI API with the given prompt and return the response.
    """
    # Replace with your actual Mistral AI API endpoint and API key
    api_endpoint = "https://api.mistral.example.com/generate"
    api_key = "your_api_key_here"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    data = {"prompt": prompt}

    response = requests.post(api_endpoint, headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        click.echo(response_data.get("response", "No response received"))
    else:
        click.echo(f"Error: {response.status_code} - {response.text}")


if __name__ == "__main__":
    call_mistral_ai()
