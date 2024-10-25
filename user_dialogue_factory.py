# coding=utf-8
import enum
from typing import Optional

from llm.llm_tools import generate_by_openai
from tools import load_data, extract_json


class DialogueType(enum.Enum):
    LLM = 1
    CSV = 2


current_type = DialogueType.CSV


def __llm_dialogue__(model: str, msg: str, temperature: float = 1) -> Optional[str]:
    prompt = f"""You are an AI assistant responsible for generating concise, relevant, and diverse quick reply options for human users.
Generate quick reply options based on the following AI response. Please consider these parameters:
1. Maximum length for each reply: 500 characters
2. Minimum Length for each reply: 200 characters
3. Tone: Friendly and professional
4. Diversity: Ensure replies cover different purposes (e.g., gratitude, questions, confirmation)
5. Relevance: Replies should be closely related to the content of the AI answer
6. Note: Write only in internet RP style, italicize actions, and avoid quotation marks. Use markdown. Be proactive, creative, and drive the plot and conversation forward. 
7. Your task is to create quick replies that match the language of the original AI answer.
Please output in JSON format, containing only the reply content.
AI answer:
{msg}
Your character:
A normal person
"""
    prompt += """Please output according to the following JSON format:
{
    "reply": "Reply content"
}"""

    messages = [
        {
            "role": "user",
            "content": f"{prompt}"
        }
    ]
    try:
        output = generate_by_openai(model, messages, temperature=temperature)
        result = extract_json(output)
        return result['reply']
    except:
        return None


def __csv_dialogue__(index: int) -> str:
    dialogue = load_data('test_case/dialogue.csv', ['content'])
    return dialogue[index % len(dialogue)]['content']


def fetch_dialogue(index: int, msg: str, dialogue_type: DialogueType = current_type) -> str:
    if dialogue_type == DialogueType.LLM:
        llm_result = __llm_dialogue__(model='claude-3-5-sonnet-20241022', msg=msg, temperature=0.5)
        if llm_result:
            return llm_result
        return __csv_dialogue__(index)
    if dialogue_type == DialogueType.CSV:
        return __csv_dialogue__(index)


if __name__ == '__main__':
    result = fetch_dialogue(
        201,
        "kiss me",
        DialogueType.CSV
    )
    print(result)
