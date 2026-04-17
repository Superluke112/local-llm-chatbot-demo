# Local LLM Chatbot Demo

A lightweight local chatbot prototype built with Python and Ollama.  
It supports multi-turn conversation with a sliding-window memory mechanism, allowing a local large language model to maintain limited conversational context in a simple and reproducible way.

## Features

- Local LLM inference through the Ollama chat API
- Multi-turn conversation support
- Sliding-window context management
- Error handling for connection, timeout, and invalid responses
- Simple command-line interface for quick testing

## Tech Stack

- Python
- Requests
- Ollama
- Local LLM model (for example, Gemma 3)

## Project Structure

local-llm-chatbot-demo/
├── local_chatbot.py
└── README.md

## How It Works

The chatbot sends user messages to a locally running Ollama model through the chat API.  
A short conversation history is stored in memory and passed back with each new request.  
To keep the implementation simple, only the most recent messages are retained using a sliding-window approach.

This means the chatbot can handle short multi-turn conversations, while avoiding unlimited growth of the context passed to the model.

## Requirements

Before running the project, make sure you have:

- Python 3 installed
- Ollama installed and running locally
- A supported model available locally, such as `gemma3`

You also need the Python package:

pip install requests

## Run the Chatbot

Start Ollama first, then run:

python local_chatbot.py

## Available Commands

- `/help` — show available commands
- `/clear` — clear conversation history
- `/history` — show current conversation history
- `exit` — quit the chatbot

## Example Use Case

This project is intended as a simple demonstration of:

- local LLM interaction
- conversation history management
- lightweight chatbot prototyping in Python

It can be used as a starting point for more advanced features such as system prompts, conversation logging, or retrieval-based memory.

## Limitations

- The chatbot only keeps a limited number of recent messages
- Conversation history is stored in memory only and is lost after the program exits
- No GUI is included; this is a command-line prototype
- The quality of responses depends on the locally installed model

## Future Improvements

Possible next steps include:

- adding a system prompt
- saving chat history to JSON
- adding a simple web interface
- supporting streaming responses
- integrating retrieval-based memory

## Author

Zhijian Song
