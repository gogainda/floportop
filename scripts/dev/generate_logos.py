#!/usr/bin/env python3
"""Generate Flop Or Top logos using Gemini API."""

import base64
import requests
import json
import os
from pathlib import Path

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY environment variable is required")
MODEL = "gemini-3-pro-image-preview"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGOS_DIR = PROJECT_ROOT / "logos"

prompts = [
    """Design a minimalist logo for "Flop Or Top" movie rating app.
    Use Gilda Display serif font style. Red (#E53935) as the primary brand color on white background.
    Clean, elegant typography with "Flop" and "Top" text. Simple and modern aesthetic.
    The logo should be professional and suitable for a movie review platform.""",

    """Create a simple logo using just the letters "F" and "T" for a movie app called "Flop Or Top".
    Use elegant serif font style like Gilda Display. Red color (#E53935) letters on clean white background.
    Minimalist design with the letters stylized or intertwined. Light, airy aesthetic.""",

    """Design a typographic logo for "FLOP OR TOP" movie rating brand.
    Gilda Display inspired serif typography. Bold red (#E53935) color scheme.
    Minimalist approach - just text, no icons. Clean white background.
    Professional, elegant, and memorable wordmark design.""",

    """Create a logo mark combining "F" and "T" initials for Flop Or Top.
    Simple geometric interpretation using red (#E53935) on white.
    Serif font influence from Gilda Display. Could include a subtle thumbs up/down concept.
    Minimalist, modern, clean design suitable for app icon."""
]

def generate_logo(prompt: str, index: int):
    """Generate a single logo using Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "responseModalities": ["IMAGE", "TEXT"]
        }
    }

    print(f"Generating logo {index + 1}...")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()

        # Extract image data from response
        for candidate in result.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "inlineData" in part:
                    image_data = part["inlineData"]["data"]
                    image_bytes = base64.b64decode(image_data)

                    filename = LOGOS_DIR / f"logo_{index + 1}.png"
                    with open(filename, "wb") as f:
                        f.write(image_bytes)
                    print(f"  Saved: {filename.relative_to(PROJECT_ROOT)}")
                    return True

        print(f"  No image in response: {result}")
        return False
    else:
        print(f"  Error {response.status_code}: {response.text}")
        return False

if __name__ == "__main__":
    LOGOS_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating Flop Or Top logos...\n")

    for i, prompt in enumerate(prompts):
        generate_logo(prompt, i)
        print()

    print("Done! Check the logos/ directory.")
