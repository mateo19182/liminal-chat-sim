import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API endpoint and headers
url = "https://api.anthropic.com/v1/messages"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": os.getenv("ANTHROPIC_API_KEY"),
    "anthropic-version": "2023-06-01"
}

# Prompt to be sent to Claude
prompt = """format the following text as in the example in the number of messages that you consider necessary. BAJO NINGUN CONCEPTO MODIFIQUES EL CONTENIDO DEL TEXTO. ejemplo: {"messages": [{"role": "system", "content": "Miguel Anxo Bastos hablando"}, {"role": "user", "content": "Ideas de Miguel Anxo Bastos sobre ..."}, {"role": "assistant", "content": "..."}]} {"messages": [{"role": "system", "content": "Miguel Anxo Bastos hablando"}, {"role": "user", "content": "Ideas de Miguel Anxo Bastos"}, {"role": "assistant", "content": "..."}]} ... texto:"""

# Function to read the text from a file
def read_text_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()

# Function to append the response to a file
def append_to_file(filename, content):
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(content + "\n\n")

# Main function
def main():
    # Read the text from a file
    input_text = read_text_from_file("input.txt")
    
    # Prepare the request payload
    payload = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 4000,
        "messages": [
            {
                "role": "user",
                "content": f"{prompt} {input_text}"
            }
        ]
    }

    # Make the API request
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        formatted_text = result['content'][0]['text']
        
        # Append the response to a file
        append_to_file("output.json", formatted_text)
        print("Response appended to output.json")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()