import chromadb
import uuid
import Gmail_Interface
from chromadb.utils import embedding_functions
import os
import dotenv

# load the environment variables
dotenv.load_dotenv()


def initialize_VectorDB():
    client = chromadb.Client()
    
    # Create an embedding function (uses OpenAI by default)
    embedding_function = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),  # or use environment variable
        model_name="text-embedding-3-small"
    )
    
    # Create collection with embedding function
    collection = client.create_collection(
        name="emails",
        embedding_function=embedding_function
    )
    return collection

def add_emails_to_vectorDB(collection, email_objects):
    """
    Add Email objects to the vector database with automatic embeddings.
    
    Args:
        collection: ChromaDB collection
        email_objects: List of Email objects (from Gmail_Interface.Email class)
    """
    if not email_objects:
        return []
    
    # Extract data from Email objects
    emails = [email.text for email in email_objects]
    from_addresses = [email.sender for email in email_objects]
    subjects = [email.subject for email in email_objects]

    emails = [Gmail_Interface.prepend_with_title(
        "Subject", subject, email) for subject, email in zip(subjects, emails)]
    
    # Generate unique IDs for each email
    ids = [str(uuid.uuid4()) for _ in email_objects]
    
    # Create metadata for each email
    metadatas = []
    for i in range(len(email_objects)):
        metadata = {
            "from_address": from_addresses[i],

        }
        metadatas.append(metadata)
    
    # Now ChromaDB will automatically generate embeddings
    collection.add(
        documents=emails,
        ids=ids,
        metadatas=metadatas
    )
    
    return ids

def query_vectorDB_combined(collection, query_text, sender=None, n_results=1):
    """Search email body text with optional sender filtering"""
    where_conditions = {}
    
    if sender:
        where_conditions["from_address"] = sender
    
    results = collection.query(
        query_texts=[query_text],  # Search the email body text
        n_results=n_results,
        where=where_conditions if where_conditions else None  # Apply metadata filters
    )
    
    return results

def extract_body_text_from_results(results):
    """Extract body text from ChromaDB query results
    
    Args:
        results: Dictionary returned from collection.query() containing documents, metadatas, distances, etc.
        
    Returns:
        list: List of body text strings from the documents
    """
    if not results or 'documents' not in results:
        return []
    
    # ChromaDB returns documents as a list of lists (one list per query)
    # Since we typically query with one query_text, we take the first list
    if results['documents'] and len(results['documents']) > 0:
        return results['documents'][0]
    
    return []

def extract_from_address_from_results(results):
    """Extract from_address from ChromaDB query results
    
    Args:
        results: Dictionary returned from collection.query() containing documents, metadatas, distances, etc.
        
    Returns:
        str: From address string from the first result's metadata, or empty string if not found
    """
    if not results or 'metadatas' not in results:
        return ""
    
    # ChromaDB returns metadatas as a list of lists (one list per query)
    # Since we typically query with one query_text, we take the first list
    if results['metadatas'] and len(results['metadatas']) > 0 and len(results['metadatas'][0]) > 0:
        metadata = results['metadatas'][0][0]  # First result from first query
        return metadata.get('from_address', '')
    
    return ""

