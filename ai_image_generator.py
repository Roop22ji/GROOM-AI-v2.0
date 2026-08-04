from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

print("Token found:", bool(HF_TOKEN))

client = InferenceClient(
    provider="hf-inference",
    api_key=HF_TOKEN
)

def generate_ai_image(prompt):

    print("Generating:", prompt)

    image = client.text_to_image(
        prompt,
        model="black-forest-labs/FLUX.1-schnell"
    )

    filename = "static/generated.png"
    image.save(filename)

    return "/" + filename