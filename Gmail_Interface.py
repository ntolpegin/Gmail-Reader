import os
import pickle
import datetime
import base64
import re
import AI_API

# if I kill load_dotenv, I can kill this line too 
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from google.auth.transport.requests import Request

# Gain full access to Gmail
SCOPES = ['https://mail.google.com/']

# Load environment variables
load_dotenv()

class Email:
    def __init__(self, sender, subject, text, token_count):
        self.sender = sender
        self.subject = subject
        self.text = text
        self.token_count = token_count

# ------------------------------Getting Text from email ------------------------------
def get_text_from_part(part, cond):
    # I left the if statements in to make the code more reliable in case the function is called elsewhere
    if part.get('mimeType') == cond:
        # Get body data and decode if needed
        body_data = part.get('body', {}).get('data')
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode('utf-8')

    return None

def find_first_multipart_alternative(parts, cond):
    """
    Find the first multipart/alternative in the parts structure and extract its text/plain content.
    Args:
        parts: The parts structure from a Gmail message payload
    Returns:
        str: Plain text content if found, None otherwise
    """
    # Base case - if parts is not a list/dict, return None
    if not isinstance(parts, (list, dict)):
        return None
    
    # If parts is a dict, check if it's multipart/alternative
    if isinstance(parts, dict):
        if parts.get('mimeType') == 'multipart/alternative':
            # Found multipart/alternative, look for text/plain in its parts
            if 'parts' in parts:
                for part in parts['parts']:
                    text = get_text_from_part(part, cond)
                    if text:
                        return text
        # If not multipart/alternative, recursively check its parts
        if 'parts' in parts:
            return find_first_multipart_alternative(parts['parts'], cond)
    
    # If parts is a list, check each part
    if isinstance(parts, list):
        for part in parts:
            result = find_first_multipart_alternative(part, cond)
            if result:
                return result
                
    return None

def find_first_multipart_mixed_or_related(parts, cond):
    """
    Find the first multipart/mixed or multipart/related in the parts structure and extract its text/plain content.
    Args:
        parts: The parts structure from a Gmail message payload
    Returns:
        str: Plain text content if found, None otherwise
    """
    # Base case - if parts is not a list/dict, return None
    if not isinstance(parts, (list, dict)):
        return None
    
    # If parts is a dict, check if it's multipart/mixed or multipart/related
    if isinstance(parts, dict):
        if parts.get('mimeType') in ['multipart/mixed', 'multipart/related']:
            # Found multipart/mixed or related, look for text/plain in its parts
            if 'parts' in parts:
                for part in parts['parts']:
                    text = get_text_from_part(part, cond)
                    if text:
                        return text
        # If not multipart/mixed or related, recursively check its parts
        if 'parts' in parts:
            return find_first_multipart_mixed_or_related(parts['parts'], cond)
    
    # If parts is a list, check each part
    if isinstance(parts, list):
        for part in parts:
            result = find_first_multipart_mixed_or_related(part, cond)
            if result:
                return result
                
    return None

def get_plain_text_body(message, cond):
    """
    Extract the plain text body from a Gmail message.
    Args:
        message: Gmail message object containing payload data
    Returns:
        str: Plain text body of the message, or None if not found
    """
    if 'payload' not in message:
        return None
    
    payload = message.get('payload', {})

    # Check if the payload itself is text/plain
    if payload.get('mimeType') == cond:
        body_data = payload.get('body', {}).get('data')
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode('utf-8')

    mess  = find_first_multipart_alternative(payload, cond)

    if mess is None:
        mess = find_first_multipart_mixed_or_related(payload, cond)

        if mess is None:
            parts = payload.get('parts', [])
            if isinstance(parts, list):
                for part in parts:
                    mess = get_plain_text_body(part, cond)
                    if mess:
                        return mess

    return mess

def plain_clean(text):
    text = AI_API.clean_email_text(text)
    return text

def html_clean(text):
    from bs4 import BeautifulSoup
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    
    # Remove images
    for img in soup.find_all('img'):
        img.decompose()
        
    # Remove style tags and their contents
    for style in soup.find_all('style'):
        style.decompose()
        
    # Remove script tags and their contents  
    for script in soup.find_all('script'):
        script.decompose()
        
    # Remove all attributes from remaining tags except href on links
    for tag in soup.find_all(True):
        if tag.name == 'a':
            href = tag.get('href', None)
            tag.attrs = {'href': href} if href else {}
        else:
            tag.attrs = {}
    
    # Get text content, preserving some whitespace/structure
    text = soup.get_text(separator=' ', strip=True)

    '''text = AI_API.clean_email_text(text)'''
    return text

def get_clean_plain_text_body(message):
    """
    Extract and clean the plain text body from a Gmail message.
    
    Args:
        message: Gmail message object containing payload data
    Returns:
        str: Cleaned plain text body of the message, or None if not found
    """
    raw_text = get_plain_text_body(message, 'text/html')



    if raw_text is None:
        raw_text = get_plain_text_body(message, 'text/plain')
        if raw_text is None:
            return None
        else:
            return plain_clean(raw_text)
    else:
        return html_clean(raw_text)

# ------------------------------ Helper Functions ------------------------------
def get_own_email_address(service):
    profile = service.users().getProfile(userId='me').execute()
    return profile['emailAddress']

def get_sender_from_message(message):
    """
    Extract the sender from a Gmail message.
    Args:
        message: Gmail message object containing payload data
    Returns:
        str: Sender of the message, returns None if not found
    """

    # Get the headers from the message
    headers = message.get('payload', {}).get('headers', [])
    for header in headers:
        if header.get('name') == 'From':
            return header.get('value')
    return None

def get_subject_from_message(message):
    """
    Extract the subject from a Gmail message.
    Args:
        message: Gmail message object containing payload data
    Returns:
        str: Subject of the message, returns None if not found
    """
    headers = message.get('payload', {}).get('headers', [])
    for header in headers:
        if header.get('name') == 'Subject':
            return header.get('value')
    return None

def count_unread_emails(service):
    """
    Count the number of unread emails in the Gmail inbox.
    Args:
        service: Gmail API service instance
    Returns:
        int: Number of unread emails found
    """
    try:
        # Query for unread messages
        results = service.users().messages().list(
            userId='me',
            q='is:unread'
        ).execute()
        
        # Get the messages list, return 0 if none found
        messages = results.get('messages', [])
        return len(messages)
        
    except Exception as e:
        print(f"Error counting unread emails: {e}")
        return 0

def send_email(service, message_text):
    """
    Send an email using the Gmail API.

    :param service: Authorized Gmail API service instance
    :param message_text: Email body
    """
    # 1. Create MIME message
    message = MIMEText(message_text)
    message['to'] = get_own_email_address(service)
    message['subject'] = "[Gmail Reader] Email Summary"

    # 2. Encode the message in base64url format
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    # 3. Build the message payload
    create_message = {
        'raw': encoded_message
    }

    # 4. Send the message
    try:
        sent_message = service.users().messages().send(userId='me', body=create_message).execute()
        return
    except Exception as e:
        return


def get_unread_emails(service, max_results=100):
    # List unread messages in the inbox
    results = service.users().messages().list(
        userId='me',
        q='label:UNREAD label:INBOX',
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])
    emails = []

    for msg in messages:
        msg_id = msg['id']
        msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

        emails.append(msg_data)

    return emails

def prepend_with_title(title, title_content, body_text):
    """
    Add a title and its content to the top of a text body.
    
    Args:
        title (str): The title label (e.g., "Subject", "From", etc.)
        title_content (str): The content for the title (e.g., "Hello!", "john@example.com")
        body_text (str): The main body text to append after the title
        
    Returns:
        str: Formatted text with title and body
    """
    if not title_content:
        title_content = ""
    if not body_text:
        body_text = ""
    
    return f"{title}: {title_content}\n{body_text}"


def get_unread_email_objects(service, max_results=100):
    """
    Get unread emails and return them as Email objects with subject, sender, and body text.
    
    Args:
        service: Authorized Gmail API service instance
        max_results (int): Maximum number of emails to retrieve (default: 100)
        
    Returns:
        list: List of Email objects containing sender, subject, text, and token_count
    """
    # Get unread emails using existing function
    unread_emails = get_unread_emails(service, max_results)
    
    email_objects = []
    
    for message in unread_emails:
        try:
            # Extract sender using existing function
            sender = get_sender_from_message(message)
            
            # Extract subject using existing function
            subject = get_subject_from_message(message)
            
            # Extract clean body text using existing function
            body_text = get_clean_plain_text_body(message)
            
            # Calculate token count for the body text
            token_count = 0
            if body_text:
                token_count = AI_API.num_tokens_from_string(body_text)
            
            # Create Email object
            email_obj = Email(
                sender=sender or "Unknown Sender",
                subject=subject or "No Subject",
                text=body_text or "",
                token_count=token_count
            )
            
            email_objects.append(email_obj)
            
        except Exception as e:
            print(f"Error processing email: {e}")
            continue
    
    return email_objects


def create_credentials():
    creds = None
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    
    # try to gain access to Gmail
    try:
        creds = flow.run_local_server(port=0)
    # if there is an error, print the error and return
    except Exception as e:
        print(f"Error creating credentials: {e}")
        raise e
    
    # save the credentials to the token.pkl file
    try:
        with open('token.pkl', 'wb') as token:
            pickle.dump(creds, token)
    except Exception as e:
        print(f"Error saving credentials: {e}")
        print("Credentials will not be saved for future use")
    
    return creds


def start_up():
    print("Starting up...")
    creds = None

    # Checks if the token.pkl file exists, and if so, loads the credentials from it
    if os.path.exists('token.pkl'):
        try:
            with open('token.pkl', 'rb') as token:
                creds = pickle.load(token)
        except (pickle.PickleError, EOFError, FileNotFoundError) as e:
            print(f"Error loading credentials from token.pkl: {e}")
            print("Will create new credentials...")
            creds = None
            # Remove the corrupted file
            try:
                os.remove('token.pkl')
                print("Removed corrupted token.pkl file")
            except FileNotFoundError:
                pass
            try:
                creds = create_credentials()
            except Exception as e:
                print(f"Error creating credentials: {e}")
                return

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            try:
                creds.refresh(Request())
                print("Credentials refreshed successfully")
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                print("Will create new credentials...")
                creds = None
                # Remove the invalid token file
                try:
                    os.remove('token.pkl')
                    print("Removed invalid token.pkl file")
                except FileNotFoundError:
                    pass
                try:
                    creds = create_credentials()
                except Exception as e:
                    print(f"Error creating credentials: {e}")
                    return
        else:
            print("Creating new credentials...")
            if not os.path.exists('credentials.json'):
                print("Error: credentials.json file not found!")
                print("Please ensure you have downloaded your OAuth credentials from Google Cloud Console")
                return
            try:
                creds = create_credentials()
            except Exception as e:
                print(f"Error creating credentials: {e}")
                return

    # Build the Gmail service - moved outside the if block
    service = build('gmail', 'v1', credentials=creds)

    return service




''' Code No longer used:
def is_PDF(filename):
    """
    Check if a filename ends with .pdf.
    Args:
        filename: Filename to check
    Returns:
        bool: True if the filename ends with .pdf, False otherwise
    """
    return filename.lower().endswith('.pdf')

def generic_Attachment_Count(message, if_Function):
    """
    Count the number of attachments of a given type in a Gmail message.
    Args:
        message: Gmail message object containing payload data
        if_Function: Function to check if the attachment is of the given type
    Returns:
        int: Number of attachments of the given type found
    """
    def recursive_count(parts):
        count = 0
        for part in parts:
            filename = part.get("filename", "").lower()
            body = part.get("body", {})
            # If the part passes the if_Function and has an attachmentId, it's an attachment
            if if_Function(filename) and "attachmentId" in body:
                count += 1
            # Check nested parts recursively
            if "parts" in part:
                count += recursive_count(part["parts"])
        return count

    payload = message.get("payload", {})
    parts = payload.get("parts", [])
    return recursive_count(parts)


    print("Enter something (type 'end' to quit):")
    while True:
        user_input = input("> ")
        if user_input.lower() == "end":
            print("Exiting.")
            break
        elif (user_input.lower() == "send email"):
            print("what do you want sent")
            user_input = input("> ")
            send_email(service, user_input)
        elif (user_input.lower() == "get unread emails"):
            print("get unread emails")
            emails = get_unread_emails(service)
            print(emails)
        elif (user_input.lower() == "count unread emails"):
            print("count unread emails")
            num_unread = count_unread_emails(service)
            print(num_unread)
        else:
            print(f"You said: {user_input}")
    
def get_time_from_message(message):
    """
    Extract the date and time from a Gmail message.
    Args:
        message: Gmail message object containing payload data
    Returns:
        str: Date and time of the message
    """
    time = message.get('internalDate')
    time = int(time) / 1000
    return datetime.datetime.fromtimestamp(time)
'''
