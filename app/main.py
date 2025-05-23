from fastapi import FastAPI, WebSocket, WebSocketDisconnect #type:ignore
from fastapi.staticfiles import StaticFiles #type:ignore
from fastapi.responses import HTMLResponse #type:ignore
import logging
from pathlib import Path
from .core.config import get_settings
from .services.agent import Agent
from .core.database import init_db, test_db_connection, get_recent_documents
from typing import Optional
import uvicorn #type:ignore

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Regulations.gov Chat Agent")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize agent
agent = Agent()

@app.on_event("startup")
async def startup_event():
    """Initialize and test the database on startup."""
    # Test database connection
    success, doc_count = await test_db_connection()
    if not success:
        logger.error("Failed to connect to database!")
    else:
        logger.info(f"Database connection successful. Found {doc_count} documents.")

@app.get("/", response_class=HTMLResponse)
async def get_chat_page():
    """Serve the chat interface."""
    html_path = Path("templates/index.html")
    return html_path.read_text()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for chat."""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            
            # Process message with agent
            response = await agent.process_query(message)
            
            # Send response back to client
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                "success": False,
                "response": "An error occurred while processing your request."
            })
        except:
            pass

@app.get("/api/recent-documents")
async def get_recent_docs(limit: Optional[int] = 10):
    """Get the most recently added documents.
    
    Args:
        limit: Maximum number of documents to return (default: 10)
    """
    try:
        documents = await get_recent_documents(limit)
        return {
            "success": True,
            "documents": documents
        }
    except Exception as e:
        logger.error(f"Error fetching recent documents: {str(e)}")
        return {
            "success": False,
            "error": "Failed to fetch recent documents"
        }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 