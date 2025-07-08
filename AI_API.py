from dotenv import load_dotenv
from openai import OpenAI
import tiktoken
import os

# Load environment variables
# I might not need this, so may kill later
load_dotenv()

client = OpenAI()

def num_tokens_from_string(string: str, model: str = "gpt-4") -> int:
    """Returns the number of tokens in a text string for a specified model.
    
    Args:
        string (str): The text string to count tokens for
        model (str): The model to use for tokenization (default: "gpt-4")
        
    Returns:
        int: Number of tokens in the string
    """
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens





def get_response(message):
    completion = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
        {
            "role": "user",
            "content": message
        }
        ]
    )

    return completion.choices[0].message.content

def get_response_from_terminal():
    user_input = input("> ")
    return get_response(user_input)

def main():
    while True:
        response =get_response_from_terminal()
        if response == "end":
            print("Exiting.")
            break
        else:
            print("hello")
            print(get_response(response))

if __name__ == "__main__":
    main()
