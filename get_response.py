import argparse
import json
import os
import anthropic
import google.generativeai as genai
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from ai21 import AI21Client
from ai21.models.chat import ChatMessage
import time

# Load environment variables from .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AI21_API_KEY = os.getenv('AI21_API_KEY')

# Configure API clients
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
#anthropic_client = anthropic.Client(api_key=ANTHROPIC_API_KEY)

genai.configure(api_key=GEMINI_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)
#openai.api_key=OPENAI_API_KEY
ai21_clinet = AI21Client(AI21_API_KEY)

os.makedirs("./response", exist_ok=True)

# Generate response functions for each model
def get_response_openai(model_name, prompt):
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=512,
        timeout = 300
        #request_timeout=300  # 최대 대기 시간을 30초로 설정

    )
    return response.choices[0].message.content



def get_response_anthropic(model_name, prompt):
    message = anthropic_client.messages.create(
        model=model_name,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
        timeout=300  # 지원되지 않는다면 try/except로 처리

    )
    return message.content[0].text

#이걸로 바꿔서 다시 해보기. 더 공식적이라고 함.
# def get_response_anthropic(model_name, prompt):
#     # Anthropic API의 경우 프롬프트에 대화 내역을 포함시키는 방식이 일반적입니다.
#     # 예시: "Human: {prompt}\n\nAssistant:" 와 같이 구성
#     formatted_prompt = f"Human: {prompt}\n\nAssistant:"
#     response = anthropic_client.completion(
#         model=model_name,
#         prompt=formatted_prompt,
#         max_tokens_to_sample=512,
#         temperature=0.7
#     )
#     # 응답 객체의 구조는 공식 문서를 참고하여 추출
#     return response.completion



def get_response_gemini(model_name, prompt):
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text
# def get_response_gemini(model_name, prompt):
#     response = genai.generate_text(
#         model=model_name,    # 예: "models/text-bison-001"
#         prompt=prompt,
#         temperature=0.7,
#         max_output_tokens=512,
#     )
#     return response.generations[0].text

def get_response_ai21(model_name, prompt):
    response = client.chat.completions.create(
        model=model_name,
        messages=[ChatMessage(role='user', content=prompt)]
    )
    return response

# Main benchmark function
def run_benchmark_all_models(prompt_file_path, output_file_path):
    # Load prompts
    with open(prompt_file_path, "r", encoding="utf-8") as f:
        prompts_data = json.load(f)

    models = {
        #"claude-3-7-sonnet-20250219": lambda p: get_response_anthropic("claude-3-7-sonnet-20250219", p),
        #"claude-3-5-haiku-20241022": lambda p: get_response_anthropic("claude-3-5-haiku-20241022", p),
        #"claude-3-opus-20240229": lambda p: get_response_anthropic("claude-3-opus-20240229", p),
        "gpt-4o": lambda p: get_response_openai("gpt-4o", p),
        "gpt-4-turbo": lambda p: get_response_openai("gpt-4-turbo", p),
        "gpt-3.5-turbo": lambda p: get_response_openai("gpt-3.5-turbo", p), 
        #"jamba-large-1.6-2025-03" : lambda p: get_response_ai21("jamba-large-1.6", p ),
        #"jamba-mini-1.6-2025-03" : lambda p: get_response_ai21("jamba-mini-1.6", p )
        #"gemini-2.5-pro-exp-03-25": lambda p: get_response_gemini("gemini-2.5-pro-exp-03-25", p),
        #"gemini-2.0-flash": lambda p: get_response_gemini("gemini-2.0-flash", p),
        #"gemini-1.5-flash": lambda p: get_response_gemini("gemini-1.5-flash", p),
        #"gemini-1.5-flash-8b": lambda p: get_response_gemini("gemini-1.5-flash-8b", p),
    }

    results = []

    for item in tqdm(prompts_data, desc="Processing prompts"):
        prompt_id = item.get("prompt_id")
        prompt_text = item.get("prompt_text")

        for model_name, get_response in tqdm (models.items()):
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
            time.sleep(10)

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