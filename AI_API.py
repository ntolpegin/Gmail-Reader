from openai import OpenAI
import tiktoken
import os
import Gmail_Interface
import dotenv

# load the environment variables
dotenv.load_dotenv()

client = OpenAI()  # Automatically uses OPENAI_API_KEY from environment

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

def summarize_Emails(emails):
    # Process emails by prepending subject and sender information
    processed_emails = []
    for email in emails:
        # Start with the email text
        email_with_subject = Gmail_Interface.prepend_with_title("Subject", email.subject, email.text)
        # Add sender information at the very beginning
        email_with_metadata = Gmail_Interface.prepend_with_title("From", email.sender, email_with_subject)
        processed_emails.append(email_with_metadata)
    
    # Now summarize the processed emails
    return summarize_array(processed_emails)

def summarize_array(array, depth=0):
    '''
    Summarize an array of strings into a single string using recursive chunking.
    
    Args:
        array (list): List of strings to summarize
        
    Returns:
        str: Single summarized string
    '''
    if not array:
        return ""
    
    # Add depth protection
    if depth > 5:  # Prevent infinite recursion
        return "Summary truncated due to recursion limit."
    
    # Define token limits (leaving buffer for prompt and response)
    MAX_TOKENS = 5000  # Conservative limit for gpt-4
    
    # First, handle individual strings that are too long
    processed_strings = []
    for text in array:
        if num_tokens_from_string(text) > MAX_TOKENS:
            # Split oversized text into chunks
            chunks = split_text_into_chunks(text, MAX_TOKENS)
            # Recursively summarize the chunks
            chunk_summary = summarize_array(chunks, depth + 1)
            processed_strings.append(chunk_summary)
        else:
            processed_strings.append(text)
    
    # Now combine strings until we hit the token limit
    combined_chunks = []
    current_chunk = ""
    
    for text in processed_strings:
        # Check if adding this text would exceed the limit
        test_chunk = current_chunk + "\n\n--- Email ---\n" + text if current_chunk else text
        
        if num_tokens_from_string(test_chunk) > MAX_TOKENS:
            if current_chunk:
                combined_chunks.append(current_chunk)
                current_chunk = text
            else:
                # Single text is too long, this shouldn't happen after preprocessing
                combined_chunks.append(text)
        else:
            current_chunk = test_chunk
    
    # Add the last chunk if it exists
    if current_chunk:
        combined_chunks.append(current_chunk)
    
    # If we only have one chunk, summarize it directly
    if len(combined_chunks) == 1:
        return summarize_text(combined_chunks[0])
    
    # If we have multiple chunks, summarize each and then recursively summarize the summaries
    summaries = []
    for chunk in combined_chunks:
        summary = summarize_text(chunk)
        summaries.append(summary)
    
    # Recursively summarize the summaries
    return summarize_array(summaries, depth + 1)

# need to test this
def split_text_into_chunks(text, max_tokens):
    """
    Split a text into chunks that fit within the token limit.
    
    Args:
        text (str): Text to split
        max_tokens (int): Maximum tokens per chunk
        
    Returns:
        list: List of text chunks
    """
    # Simple approach: split by sentences first, then by characters if needed
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        test_chunk = current_chunk + ". " + sentence if current_chunk else sentence
        
        if num_tokens_from_string(test_chunk) > max_tokens:
            if current_chunk:
                chunks.append(current_chunk + "\n\n[CHUNK_BREAK]\n")  # Add special separator
                current_chunk = sentence
            else:
                # Single sentence is too long, split by characters
                char_chunks = split_by_characters(sentence, max_tokens)
                # Add separator to all but the last chunk
                for i, chunk in enumerate(char_chunks[:-1]):
                    chunks.append(chunk + "\n\n[CHUNK_BREAK]\n")
                chunks.append(char_chunks[-1])  # Last chunk doesn't need separator
        else:
            current_chunk = test_chunk
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def split_by_characters(text, max_tokens):
    """
    Split text by characters when sentence-level splitting isn't sufficient.
    
    Args:
        text (str): Text to split
        max_tokens (int): Maximum tokens per chunk
        
    Returns:
        list: List of text chunks
    """
    chunks = []
    # Rough estimate: 1 token ≈ 4 characters
    approx_chars_per_chunk = max_tokens * 3  # Conservative estimate
    
    for i in range(0, len(text), approx_chars_per_chunk):
        chunk = text[i:i + approx_chars_per_chunk]
        chunks.append(chunk)
    
    return chunks

def summarize_text(text):
    """
    Summarize a single text using GPT.
    
    Args:
        text (str): Text to summarize
        
    Returns:
        str: Summarized text
    """
    if not text or text.strip() == "":
        return ""
    
    prompt = """Please provide a concise summary of the following email content. Focus on:
- Key topics and main points
- Important requests or actions needed
- Relevant dates, people, or deadlines mentioned
- Overall purpose/intent of the communication

Keep the summary brief but informative. The summary should be substantially shorter than the original text. 

If the text provided appears to already be a summary, limit any additional summary to one to two sentences.

Content to summarize:
"""


    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "user", 
                    "content": prompt + text
                }
            ],
            temperature=0.3
        )
        
        summary = completion.choices[0].message.content.strip()
        
        # Safety check: if summary is longer than original, truncate it
        if len(summary) > len(text):
            print(f"Warning: Summary ({len(summary)} chars) longer than original ({len(text)} chars). Truncating.")
            summary = summary[:len(text)//2]  # Make it at least half the original length
        
        return summary
    
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return text[:500]  # Return truncated version as fallback

def clean_email_text(text, max_tokens =5000, depth=0):
    """
    Clean email text with proper chunking and recursion protection.
    
    Args:
        text (str): Text to clean
        max_tokens (int): Maximum tokens allowed
        depth (int): Recursion depth to prevent infinite loops
    """    

    prompt = '''Please extract and return only the main body content from this email text. 
    
    Remove any HTML artifacts or formatting remnants. If the email is a forwarded email, treat the header data of the forwarded email as part of the body, and leave it in.
    For example, if person X forwards an email to person Y from person Z, the email address from person Z should still be included.  

    Return only the core message content that the sender actually wrote. If there's no meaningful content or there is no content at all, return an empty string.

    Email text:
    '''

    # Safeguard to prevent infinite recursion and bankrupting me with API calls
    if depth > 5:
        return text[:max_tokens*4]
    
    # Calculate available tokens for text
    prompt_tokens = num_tokens_from_string(prompt)
    available_tokens = max_tokens - prompt_tokens
    
    # If text fits, process it
    if num_tokens_from_string(text) <= available_tokens:
        try:
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "user", 
                        "content": prompt + text
                    }
                ],
                temperature=0.1
            )

            if completion.choices[0].message.content.strip() == "You didn't provide any email text. Please provide the text so I can extract the main body content.":
                return ""
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error cleaning email text: {e}")
            return text
    
    # If text is too long, split it properly
    else:
        # Use the proper chunking function
        chunks = split_text_into_chunks(text, available_tokens)
        
        if len(chunks) == 1:
            # Even after chunking, it's still too long - truncate
            return text[:available_tokens*4]  # Rough character limit
        
        # Process each chunk recursively
        cleaned_chunks = []
        for chunk in chunks:
            cleaned_chunk = clean_email_text(chunk, max_tokens, depth + 1)
            cleaned_chunks.append(cleaned_chunk)
        
        return " ".join(cleaned_chunks)

def answer_question_with_context(question, from_address, email_context, max_tokens):
    return answer_question_with_context_helper(question, Gmail_Interface.prepend_with_title("From", from_address, email_context), max_tokens)

def answer_question_with_context_helper(question, email_context, max_tokens):
    """
    Answer a user question using email context, with automatic summarization if too long.
    
    Args:
        question (str): The user's question
        email_context (str): The email context to base the answer on
        max_tokens (int): Maximum tokens allowed for the request
        
    Returns:
        str: GPT's response based on the context
    """
    # Create the prompt
    prompt = f"""Based on the following email context, please answer this question: {question}

Email Context:
{email_context}

Answer:"""
    
    # Check if the prompt fits within token limits
    prompt_tokens = num_tokens_from_string(prompt)
    
    if prompt_tokens <= max_tokens:
        # Prompt fits, send directly
        try:
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error getting response: {e}")
            return "Sorry, I couldn't process your request due to an error."
    
    else:
        # Prompt is too long, need to summarize
        # First, try summarizing just the email context
        summarized_context = summarize_text(email_context)
        
        # Create new prompt with summarized context
        new_prompt = f"""Based on the following email context summary, please answer this question: {question}

Email Context Summary:
{summarized_context}

Answer:"""
        
        # Check if this fits now
        if num_tokens_from_string(new_prompt) <= max_tokens:
            try:
                completion = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "user",
                            "content": new_prompt
                        }
                    ],
                    temperature=0.1
                )
                return completion.choices[0].message.content.strip()
            except Exception as e:
                print(f"Error getting response: {e}")
                return "Sorry, I couldn't process your request due to an error."
        
        else:
            # Even the summarized context is too long, summarize the question too

            summarized_question = question

            if num_tokens_from_string(question) <= max_tokens:
                try:
                    completion = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {
                                "role": "user",
                                "content": "Summarize this question: " + question
                            }
                        ],
                        temperature=0.1
                    )
                    summarized_question = completion.choices[0].message.content.strip()
                except Exception as e:
                    print(f"Error getting response: {e}")
                    return "Sorry, I couldn't process your request due to an error."
            
            final_prompt = f"""Based on the following email context summary, please answer this question: {summarized_question}

Email Context Summary:
{summarized_context}

Answer:"""
            
            # Final check - if this is still too long, we need to truncate aggressively
            if num_tokens_from_string(final_prompt) <= max_tokens:
                try:
                    completion = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {
                                "role": "user",
                                "content": final_prompt
                            }
                        ],
                        temperature=0.1
                    )
                    return completion.choices[0].message.content.strip()
                except Exception as e:
                    print(f"Error getting response: {e}")
                    return "Sorry, I couldn't process your request due to an error."
            else:
                # Last resort: truncate the summarized context to fit
                base_prompt = f"""Based on the following email context summary, please answer this question: {summarized_question}

Email Context Summary:
"""
                ending = "\n\nAnswer:"
                
                base_tokens = num_tokens_from_string(base_prompt + ending)
                available_tokens = max_tokens - base_tokens - 100  # Buffer for safety
                
                # Truncate the summarized context to fit
                truncated_context = truncate_text_to_tokens(summarized_context, available_tokens)
                
                final_truncated_prompt = base_prompt + truncated_context + ending

                try:
                    completion = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {
                                "role": "user",
                                "content": final_truncated_prompt
                            }
                        ],
                        temperature=0.1
                    )
                    return completion.choices[0].message.content.strip()
                except Exception as e:
                    print(f"Error getting response: {e}")
                    return "Sorry, I couldn't process your request due to an error."

def truncate_text_to_tokens(text, max_tokens):
    """
    Truncate text to fit within a specified number of tokens.
    
    Args:
        text (str): The text to truncate
        max_tokens (int): Maximum number of tokens allowed
        
    Returns:
        str: Truncated text that fits within the token limit
    """
    if num_tokens_from_string(text) <= max_tokens:
        return text
    
    # Rough approximation: 4 characters per token
    estimated_chars = max_tokens * 4
    
    # Start with rough truncation
    truncated = text[:estimated_chars]
    
    # Refine by checking actual token count and adjusting
    max_iterations = 100
    iteration_count = 0
    while num_tokens_from_string(truncated) > max_tokens and len(truncated) > 0 and iteration_count < max_iterations:
        truncated = truncated[:int(len(truncated) * 0.9)]
        iteration_count += 1
    
    return truncated

'''
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
'''