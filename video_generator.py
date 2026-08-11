import os
from huggingface_hub import InferenceClient

HF_TOKEN = "PASTE_YOUR_HUGGING_FACE_TOKEN_HERE"

client = InferenceClient(
    provider="hf-inference",
    api_key=HF_TOKEN,
)

def generate_video(prompt):
    video = client.text_to_video(prompt)

    os.makedirs("static", exist_ok=True)
    output_path = "static/generated_video.mp4"

    with open(output_path, "wb") as f:
        f.write(video)

    return output_path