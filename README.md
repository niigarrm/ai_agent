# Personal Assistant Agent

A simple command-line AI assistant built in Python.  
It uses **Gemini** for general conversation and **local tools** for selected tasks such as calculations, so basic utility features can still work even if the model is unavailable.

## Features

- Chat with an AI assistant from the terminal
- Local calculator tool for arithmetic expressions
- Local-first routing for supported tools
- Graceful handling of Gemini quota/rate-limit errors
- Conversation reset with `clear`
- Clean CLI loop with `exit` support
- Extensible structure for adding more tools later

## How it works

The agent processes user input in this order:

1. It checks whether the request matches a supported **local tool**
2. If yes, it handles the request locally
3. If not, it sends the message to **Gemini**

This means requests like:

- `calculate 2+2`
- `what is 7*8?`
- `solve (2+3)*4`

are handled locally and do **not** depend on Gemini.

## Tech stack

- Python
- Google Gemini API
- `google-generativeai`
- `ast` for safe arithmetic parsing
- Regular expressions for tool routing

## Project structure

Example structure:

```bash
.
├── main.py
├── requirements.txt
├── .env
└── README.md
