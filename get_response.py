import argparse
import json
import os
import anthropic
import google.generativeai as genai
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure API clients
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

os.makedirs("./response", exist_ok=True)

# Generate response functions for each model
def get_response_openai(model_name, prompt):
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=512
    )
    return response.choices[0].message.content


def get_response_anthropic(model_name, prompt):
    message = anthropic_client.messages.create(
        model=model_name,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def get_response_gemini(model_name, prompt):
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text

# Main benchmark function
def run_benchmark_all_models(prompt_file_path, output_file_path):
    # Load prompts
    with open(prompt_file_path, "r", encoding="utf-8") as f:
        prompts_data = json.load(f)

    models = {
        "claude-3-5-haiku-20241022": lambda p: get_response_anthropic("claude-3-5-haiku-20241022", p),
        "claude-3-7-sonnet-20250219": lambda p: get_response_anthropic("claude-3-7-sonnet-20250219", p),
        "gpt-4o": lambda p: get_response_openai("gpt-4o", p),
        "gpt-4-turbo": lambda p: get_response_openai("gpt-4-turbo", p),
        #"gemini-2.0-flash": lambda p: get_response_gemini("gemini-2.0-flash", p),
        #"gemini-1.5-flash": lambda p: get_response_gemini("gemini-1.5-flash", p),
    }

    results = []

    for item in tqdm(prompts_data, desc="Processing prompts"):
        prompt_id = item.get("prompt_id")
        prompt_text = item.get("prompt_text")

        for model_name, get_response in models.items():
            try:
                reply = get_response(prompt_text)

                result_item = {
                    "prompt_id": prompt_id,
                    "model_name": model_name,
                    "assistant_reply": reply,
                }

            except Exception as e:
                result_item = {
                    "prompt_id": prompt_id,
                    "model_name": model_name,
                    "assistant_reply": f"Error occurred: {str(e)}",
                }

            results.append(result_item)

      # 결과를 ./response 폴더에 저장
    with open(output_file_path, "w", encoding="utf-8") as out_f:
        json.dump(results, out_f, indent=2, ensure_ascii=False)

    print(f"Benchmark complete! Results saved to: {output_file_path}")

def get_unique_filename(directory, base_filename):
    base_path = os.path.join(directory, base_filename + ".json")
    if not os.path.exists(base_path):
        return base_path
    
    # 이미 존재할 경우 숫자 붙여서 파일명 결정
    num = 1
    while True:
        new_filename = f"{base_filename}_{num}.json"
        new_path = os.path.join(directory, new_filename)
        if not os.path.exists(new_path):
            return new_path
        num += 1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default="cannabis", help="JSON file path containing original prompts")
    parser.add_argument("--region", default="korea", help="Input JSON file path")
    args = parser.parse_args()

    prompt_file = os.path.join("./benchmark", f"{args.category}.json")
    
    directory = os.path.join("./response", args.category)
    os.makedirs(directory, exist_ok=True)  # 디렉토리 자동생성

    base_filename = f"{args.category}_{args.region}"
    result_file = get_unique_filename(directory, base_filename)

    run_benchmark_all_models(prompt_file, result_file)

if __name__ == "__main__":
    main()