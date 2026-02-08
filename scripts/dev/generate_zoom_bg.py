#!/usr/bin/env python3
"""Generate Zoom background with Flop Or Top logo in corner."""

import base64
import requests
import os
from pathlib import Path

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY environment variable is required")
MODEL = "gemini-3-pro-image-preview"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGOS_DIR = PROJECT_ROOT / "logos"

prompt = """Create a Zoom video call background (16:9 aspect ratio, 1920x1080).
Pure white background, completely plain and clean.
Place a "FLOP OR TOP" logo in the TOP LEFT corner - red serif text (#E53935),
stacked layout with FLOP on top, small "or" in the middle, TOP on bottom.
The logo should be medium-sized (about 20-25% of the image width),
positioned in the upper left corner with some padding from edges.
The rest of the background must be completely plain white, no decoration, no texture, no objects.
Simple minimalist design."""

def generate_zoom_background():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

    headers = {"Content-Type": "application/json"}

    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
    }

    print("Generating Zoom background...")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        for candidate in result.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "inlineData" in part:
                    image_data = part["inlineData"]["data"]
                    image_bytes = base64.b64decode(image_data)

                    filename = LOGOS_DIR / "zoom_background.png"
                    with open(filename, "wb") as f:
                        f.write(image_bytes)
                    print(f"Saved: {filename.relative_to(PROJECT_ROOT)}")
                    return True
        print(f"No image in response: {result}")
        return False
    else:
        print(f"Error {response.status_code}: {response.text}")
        return False

if __name__ == "__main__":
    LOGOS_DIR.mkdir(parents=True, exist_ok=True)
    generate_zoom_background()
