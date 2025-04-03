# gpt.py

import requests
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference.models import UserMessage
from azure.ai.inference.models import SystemMessage
from azure.ai.inference import ChatCompletionsClient
import os
from openai import OpenAI
from dotenv import load_dotenv
from set_prompt import bot_prompt  # general_prompt

load_dotenv()
api_key = os.getenv("GPT4_TOKEN")


def ask_gpt(prompt: str) -> str:
    try:
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=api_key,
        )

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": bot_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4o",
            temperature=1,
            max_tokens=4096,
            top_p=1
        )

        return response.choices[0].message.content


    except Exception as e:
        print(f"Error calling GPT: {e}")
        return "🚨 Sorry, something went wrong while talking to the assistant."
    
# api_key = os.getenv("LLAMA33_TOKEN")


# def ask_gpt(prompt: str) -> str:
#     try:
#         endpoint = "http://localhost:11434/api/generate"

#         data = {
#             "model": "gemma3:12b",  # Replace with the model you have
#             "prompt": f"{bot_prompt}\n {prompt}",
#             "prompt": bot_prompt.format(general_prompt, None, None, prompt),
#             "stream": False  # Set to True for streaming responses
#         }

#         response = requests.post(endpoint, json=data)
        
#         final_return = response.json()['response']
#         # print(response.json()['response'])

#         print(f"here: {data['prompt']}")

#         return final_return

#     except Exception as e:
#         print(f"Error calling GPT: {e}")
#         return "🚨 Sorry, something went wrong while talking to the assistant."


# def ask_gpt(prompt: str) -> str:
#     try:
#         client = ChatCompletionsClient(
#         endpoint="https://models.inference.ai.azure.com",
#         credential=AzureKeyCredential(api_key),
#     )

#         response = client.complete(
#             messages=[
#                 SystemMessage(bot_prompt),
#                 UserMessage(prompt)
#             ],
#             model="Llama-3.3-70B-Instruct",
#             temperature=0.8,
#             max_tokens=2048,
#             top_p=0.1
#         )

#         return response.choices[0].message.content


#     except Exception as e:
#         print(f"Error calling GPT: {e}")
#         return "🚨 Sorry, something went wrong while talking to the assistant."



