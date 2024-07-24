import re

def format_text(text):
    # Split the text into lines
    lines = text.split('\n')
    
    # Remove extra blank lines
    lines = [line.strip() for line in lines if line.strip()]
    
    # Join short lines that are part of the same sentence
    formatted_lines = []
    current_sentence = []
    for line in lines:
        current_sentence.append(line)
        if line.endswith(('.', '?', '!')):
            formatted_lines.append(' '.join(current_sentence))
            current_sentence = []
    if current_sentence:
        formatted_lines.append(' '.join(current_sentence))
    
    # Capitalize the first letter of each sentence, add proper punctuation, and substitute quotes
    for i, line in enumerate(formatted_lines):
        line = line.capitalize()
        if not line.endswith(('.', '?', '!')):
            line += '.'
        # Substitute double quotes for single quotes
        line = re.sub(r'"', "'", line)
        formatted_lines[i] = line
    
    return '\n\n'.join(formatted_lines)

# Read input from file
input_file = 'vid.txt'
try:
    with open(input_file, 'r', encoding='utf-8') as file:
        input_text = file.read()
except FileNotFoundError:
    print(f"Error: The file '{input_file}' was not found.")
    exit(1)
except IOError:
    print(f"Error: There was an issue reading the file '{input_file}'.")
    exit(1)

# Format the text
formatted_text = format_text(input_text)

# Write the formatted text to a new file
output_file = 'vid_formatted.txt'
try:
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(formatted_text)
    print(f"Formatted text has been written to '{output_file}'.")
except IOError:
    print(f"Error: There was an issue writing to the file '{output_file}'.")
    exit(1)

# Print the formatted text to console
print("\nFormatted Text:")
print(formatted_text)