import os
import pickle
import datetime
import base64

# if I kill load_dotenv, I can kill this line too 
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from google.auth.transport.requests import Request

# Gain full access to Gmail
SCOPES = ['https://mail.google.com/']


# think about redoing this using client libraries


# Load environment variables
# I might not need this, so may kill later
load_dotenv()

def get_text_from_part(part):
    # I left the if statements in to make the code more reliable in case the function is called elsewhere
    if part.get('mimeType') == 'text/plain':
        # Get body data and decode if needed
        body_data = part.get('body', {}).get('data')
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode('utf-8')

    return None

def find_first_multipart_alternative(parts):
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
                    text = get_text_from_part(part)
                    if text:
                        return text
        # If not multipart/alternative, recursively check its parts
        if 'parts' in parts:
            return find_first_multipart_alternative(parts['parts'])
    
    # If parts is a list, check each part
    if isinstance(parts, list):
        for part in parts:
            result = find_first_multipart_alternative(part)
            if result:
                return result
                
    return None

def find_first_multipart_mixed_or_related(parts):
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
                    text = get_text_from_part(part)
                    if text:
                        return text
        # If not multipart/mixed or related, recursively check its parts
        if 'parts' in parts:
            return find_first_multipart_mixed_or_related(parts['parts'])
    
    # If parts is a list, check each part
    if isinstance(parts, list):
        for part in parts:
            result = find_first_multipart_mixed_or_related(part)
            if result:
                return result
                
    return None

def get_plain_text_body(message):
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
    if payload.get('mimeType') == 'text/plain':
        body_data = payload.get('body', {}).get('data')
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode('utf-8')

    mess  = find_first_multipart_alternative(payload)

    if mess is None:
        mess = find_first_multipart_mixed_or_related(payload)

        if mess is None:
            parts = payload.get('parts', [])
            if isinstance(parts, list):
                for part in parts:
                    mess = get_plain_text_body(part)
                    if mess:
                        return mess

    return mess

def get_own_email_address(service):
    profile = service.users().getProfile(userId='me').execute()
    return profile['emailAddress']

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
    message['subject'] = "[Automated Response] Email Summary"

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

def create_credentials():
    creds = None
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    
    # try to gain access to Gmail
    try:
        creds = flow.run_local_server(port=0)
        print("New credentials created successfully")
    # if there is an error, print the error and return
    except Exception as e:
        print(f"Error creating credentials: {e}")
        raise e
    
    # save the credentials to the token.pkl file
    try:
        with open('token.pkl', 'wb') as token:
            pickle.dump(creds, token)
        print("Credentials saved to token.pkl")
    except Exception as e:
        print(f"Error saving credentials: {e}")
        print("Credentials will not be saved for future use")
    
    return creds


def main():
    print("starting")
    creds = None

    # Checks if the token.pkl file exists, and if so, loads the credentials from it
    if os.path.exists('token.pkl'):
        print("Loading credentials from token.pkl")
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
    print("building the service")
    service = build('gmail', 'v1', credentials=creds)

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


if __name__ == "__main__":
    main()
