README.txt 

Remember to run the following commands to restart the virtual environment:

source venv/bin/activate



Please see below for the commmands to install the dependencies:

pip install -r requirements.txt


# Email Assistant with AI-Powered Features

This program is an intelligent email management system that integrates with Gmail to provide AI-powered analysis and automation capabilities.

## Features

### Core Functionality
- **Email Reading**: Connects to Gmail to fetch and read unread emails
- **AI Summarization**: Automatically summarizes individual emails or groups of emails
- **Smart Email Search**: Ask questions about specific emails using vector database search
- **Email Composition**: Send emails directly through the interface

### Available Commands
- `send an email` - Compose and send an email to yourself
- `summarize emails` - Get AI-generated summaries of your unread emails
- `I'd like to ask a question about a specific email` - Query specific emails by sender or content
- `send summary email` - Generate and email yourself a summary of your unread emails
- `restart` - Reinitialize all services and refresh email data
- `help` - Display available commands
- `exit` - Quit the program

### Technical Components
- **Gmail API Integration**: Handles authentication and email operations
- **OpenAI GPT Integration**: Powers text summarization and question answering
- **Vector Database**: Enables semantic search across email content
- **Text Processing**: Cleans and processes HTML/plain text email content

## How It Works
1. The program authenticates with your Gmail account
2. Fetches unread emails and processes their content
3. Stores email data in a vector database for fast searching
4. Provides an interactive command-line interface for various operations
5. Uses AI to understand and respond to your queries about email content

This tool is particularly useful for managing large volumes of emails and quickly extracting key information without manually reading through everything.
