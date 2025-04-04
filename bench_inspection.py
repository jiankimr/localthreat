import argparse
from openai import OpenAI

import json
import os
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)
                
def moderate_text(text):
    response = client.moderations.create(input=text)
    scores = response.results[0].category_scores
    flagged = response.results[0].flagged
    # dict로 변환하여 반환
    scores_dict = scores.model_dump()  # Pydantic v2 기준 (최신)
    # 만약 model_dump() 오류 시 scores.dict() 사용 (Pydantic v1)
    # None값을 0으로 치환
    scores_dict = {k: (v if v is not None else 0.0) for k, v in scores_dict.items()}
    return scores_dict, flagged

def calculate_scores(input_json):
    with open(input_json, "r", encoding="utf-8") as file:
        prompts = json.load(file)

    total_score_sum = 0

    for prompt in tqdm(prompts, desc="Moderating prompts"):
        scores, flagged = moderate_text(prompt["prompt_text"])
        prompt["moderation_scores"] = scores
        prompt["moderation_flagged"] = flagged
        prompt["total_moderation_score"] = sum(scores.values())
        total_score_sum += prompt["total_moderation_score"]

    overall_average = total_score_sum / len(prompts)

    output_json = {
        "overall_average_moderation_score": overall_average,
        "prompts": prompts
    }

    return output_json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default="cannabis", help="원본 프롬프트 JSON 파일 경로")
    args = parser.parse_args()

    input_filename = f"./benchmark/{args.category}.json"

    os.makedirs("./benchmark/toxicity", exist_ok=True)  
    output_filename = f"./benchmark/toxicity/{args.category}_toxicity.json"

    result = calculate_scores(input_filename)

    with open(output_filename, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)

    print(f"Moderation results saved to {output_filename}")

if __name__ == "__main__":
    main()