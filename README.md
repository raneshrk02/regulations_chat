# RAG LLM Agent for Federal Regulations

A Retrieval-Augmented Generation (RAG) system that provides intelligent access to Federal Regulations using a local LLM through Ollama. The system features a real-time chat interface, document retrieval, and natural language processing capabilities.

## Features

- **Real-time Chat Interface**: WebSocket-based chat system for instant responses
- **Document Retrieval**: Efficient search and retrieval of federal regulations
- **Local LLM Integration**: Uses Ollama with the Qwen model for processing
- **RAG Implementation**: Combines document retrieval with LLM-generated responses
- **Federal Register API Integration**: Automatically fetches and updates document database
- **Modern Web Interface**: Clean, responsive design with typing indicators

## Prerequisites

- Python 3.8 or higher
- MySQL 8.0 or higher
- [Ollama](https://ollama.ai/) installed with the Qwen model

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/raneshrk02/regulations_chat
   cd regulations_chat
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:
   ```env
   # Database settings
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=regulations_db

   # Ollama settings
   OLLAMA_API_URL=http://localhost:11434/api/generate
   MODEL_NAME=qwen:0.5b

   # App settings
   APP_HOST=0.0.0.0
   APP_PORT=8000
   DEBUG=True
   ```

## Setup

1. Install and start MySQL server

2. Install Ollama and pull the Qwen model:
   ```bash
   # Install Ollama from https://ollama.ai/
   ollama pull qwen:1b
   ```

3. Initialize the database and fetch initial documents:
   ```bash
   python run_pipeline.py
   ```

4. Start the application:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Project Structure

```
.
|-- app/
|   |-- core/
|   |   |-- config.py
|   |   |-- database.py
|   |
|   |-- models/
│   |   |-- schemas.py
|   |
|   |-- services/
|   |   |-- agent.py
|   |   |-- data_pipeline.py
|   |
|   |-- main.py
|
|-- static/
|   |-- styles.css
|   
|-- templates/
|   |-- index.html
|   
|-- .env
|-- README.md
|-- requirements.txt
```

## Usage

1. **Data Pipeline**
   - Run `python run_pipeline.py` to fetch and update documents
   - By default, fetches documents from the last 120 days
   - Automatically creates and updates the database schema

2. **Chat Interface**
   - Access the web interface at `http://localhost:8000`
   - Ask questions about federal regulations
   - View real-time responses with document citations

3. **API Endpoints**
   - `GET /`: Main chat interface
   - `GET /api/recent-documents`: Get most recent documents
   - `WebSocket /ws`: Chat communication endpoint

## Query Examples

1. Recent Documents:
   ```
   "What are the most recent documents in the database?"
   ```

2. Specific Topics:
   ```
   "Find regulations about healthcare policy"
   "What are the latest environmental protection rules?"
   ```

3. Document Details:
   ```
   "Tell me more about document [FR-2024-XXXX]"
   ```

## Response Format

The system provides structured responses including:
- Direct answers to queries
- Document citations with document numbers
- Publication dates and relevant excerpts
- Agency information and context

## Troubleshooting

1. **Database Connection Issues**
   - Verify MySQL is running
   - Check credentials in `.env`
   - Ensure database exists

2. **Ollama Connection**
   - Verify Ollama is running (`ollama serve`)
   - Check if Qwen model is installed
   - Confirm OLLAMA_API_URL is correct

3. **API Rate Limits**
   - Using DEMO_KEY has limited requests
   - Consider getting an API key from regulations.gov