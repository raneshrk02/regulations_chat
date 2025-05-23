from pydantic import BaseModel, Field #type:ignore
from typing import List, Optional
from datetime import date

class Document(BaseModel):
    """Document model for regulatory documents."""
    id: str
    title: str
    document_number: str
    document_type: str
    publication_date: Optional[date]
    abstract: Optional[str]
    full_text: Optional[str] = None
    agencies: List[str] = Field(default_factory=list)

class DocumentResponse(BaseModel):
    """Response model for single document retrieval."""
    success: bool
    document: Document

class DocumentSearchResponse(BaseModel):
    """Response model for document search."""
    success: bool
    documents: List[Document]

class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    success: bool
    documents: List[Document]

class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str

class ChatMessage(BaseModel):
    """Chat message model."""
    role: str
    content: str

class ChatResponse(BaseModel):
    """Chat response model."""
    success: bool
    response: str
    documents: Optional[List[Document]] = None

class WebSocketMessage(BaseModel):
    """WebSocket message from client."""
    message: str
    type: str = "user"  # "user" or "system"

class WebSocketResponse(BaseModel):
    """WebSocket response to client."""
    success: bool
    response: str
    type: str = "assistant"
    documents: Optional[List[Document]] = None  # Referenced documents in the response 