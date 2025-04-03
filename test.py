import argparse
import json
import os
import openai
import anthropic
import ollama
import google.generativeai as genai
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure API clients
openai.api_key = OPENAI_API_KEY
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)

def get_response_openai(model_name="gpt-4-turbo", prompt="hello"):
    response = openai.ChatCompletion.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=512
    )
    return response["choices"][0]["message"]["content"]

print("hello")
print(get_response_openai())