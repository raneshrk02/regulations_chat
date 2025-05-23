import json
import aiohttp #type:ignore
from typing import Dict, Any, List
import logging
from ..core.config import get_settings
from ..core.database import get_db

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert assistant specializing in Federal Regulations and government documents. Your responses must be precise, factual, and based solely on the available document data provided in the context.

CORE PRINCIPLES:
1. ONLY use information from the documents provided in the context
2. Always cite specific documents using [Document Number] format
3. Never provide generic or vague responses
4. If no documents are found, clearly state: "No documents are currently available in the database."
5. Never suggest search strategies or tools to the user
6. Never make up or assume information not present in the provided documents
7. ONLY use standard English characters (A-Z, a-z) and common punctuation
8. Never include non-English characters or special symbols
9. Use only official agency names and acronyms (e.g., "Centers for Disease Control and Prevention (CDC)")

RESPONSE STRUCTURE FOR RECENT DOCUMENTS:
1. Start with: "Here are the most recent documents in the database:"
2. List documents in chronological order (newest first):
   - Publication Date: [DATE]
   - Title: [TITLE]
   - Type: [TYPE]
   - Key Points: [2-3 bullet points from abstract]
   - [Document Number]
3. End with a clear statement about the time range covered

RESPONSE STRUCTURE FOR OTHER QUERIES:
1. Direct Answer: Start with a clear statement about what documents were found
2. Document Details: For each relevant document, provide:
   - Title and publication date (using standard English characters only)
   - Key points from the abstract (properly formatted)
   - Agency names in full official format
3. Context: Synthesize the information from multiple documents if available
4. Citations: List all referenced documents at the end using [Document Number]

EXAMPLES:
❌ Bad Response:
"You can search for recent documents in various ways..."

✅ Good Response:
"Here are the most recent documents in the database:

1. Publication Date: 2024-03-15
   Title: Medicare Coverage Update 2024
   Type: Rule
   Key Points:
   - Updates payment policies for telehealth services
   - Expands mental health coverage options
   [Document CMS-2024-0123]

2. [Next most recent document...]

These documents cover the period from February 15, 2024 to March 15, 2024."

IMPORTANT:
- Always include publication dates in YYYY-MM-DD format
- List documents in chronological order (newest first)
- Use clear, professional language
- Include specific details from the documents
- Never suggest ways to search for documents
- If no documents are found, say so clearly and stop

Remember: Provide specific information from the available documents, formatted clearly and professionally."""

class Agent:
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT

    async def search_documents(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for documents in the database."""
        async with get_db() as cur:
            search_query = """
                SELECT id, title, document_number, document_type, publication_date, abstract 
                FROM documents 
                WHERE MATCH(title, abstract, full_text) AGAINST(%s IN NATURAL LANGUAGE MODE)
                LIMIT %s
            """
            await cur.execute(search_query, (query, limit))
            results = await cur.fetchall()
            return [
                {
                    'id': row[0],
                    'title': row[1],
                    'document_number': row[2],
                    'document_type': row[3],
                    'publication_date': row[4].isoformat() if row[4] else None,
                    'abstract': row[5]
                }
                for row in results
            ]

    async def get_document_details(self, doc_id: str) -> Dict:
        """Get detailed information about a specific document."""
        async with get_db() as cur:
            query = """
                SELECT id, title, document_number, document_type, publication_date, 
                       abstract, full_text, agencies 
                FROM documents 
                WHERE id = %s
            """
            await cur.execute(query, (doc_id,))
            row = await cur.fetchone()
            if row:
                return {
                    'id': row[0],
                    'title': row[1],
                    'document_number': row[2],
                    'document_type': row[3],
                    'publication_date': row[4].isoformat() if row[4] else None,
                    'abstract': row[5],
                    'full_text': row[6],
                    'agencies': json.loads(row[7]) if row[7] else []
                }
            return None

    async def get_recent_documents(self, days: int = 7) -> List[Dict]:
        """Get recent documents from the last N days."""
        async with get_db() as cur:
            query = """
                SELECT id, title, document_number, document_type, publication_date, abstract 
                FROM documents 
                WHERE publication_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                ORDER BY publication_date DESC
                LIMIT 10
            """
            await cur.execute(query, (days,))
            results = await cur.fetchall()
            return [
                {
                    'id': row[0],
                    'title': row[1],
                    'document_number': row[2],
                    'document_type': row[3],
                    'publication_date': row[4].isoformat() if row[4] else None,
                    'abstract': row[5]
                }
                for row in results
            ]

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query and return a response."""
        try:
            # Check if this is a query about recent documents
            recent_queries = ["recent", "latest", "most recent", "new", "newest"]
            is_recent_query = any(term in query.lower() for term in recent_queries)
            
            if is_recent_query:
                # Use get_recent_documents for recent document queries
                documents = await self.get_recent_documents(days=30)  # Get last 30 days
                logger.info(f"Recent documents query - Found {len(documents)} documents")
            else:
                # Use regular search for other queries
                documents = await self.search_documents(query, limit=5)
                logger.info(f"Search query - Found {len(documents)} documents")
            
            # Log the documents found
            for doc in documents:
                logger.info(f"Document: {doc['title']} ({doc['document_number']}) - {doc['publication_date']}")
            
            # Prepare document context
            doc_context = ""
            if documents:
                doc_context = "\nAvailable documents:\n"
                # Sort documents by publication date for recent queries
                if is_recent_query:
                    documents = sorted(documents, key=lambda x: x['publication_date'] if x['publication_date'] else "", reverse=True)
                
                for doc in documents:
                    # Ensure all text is properly encoded as ASCII/English
                    doc_context += f"\nDocument ID: {doc['id']}\n"
                    doc_context += f"Title: {self._clean_text(doc['title'])}\n"
                    doc_context += f"Document Number: {doc['document_number']}\n"
                    doc_context += f"Type: {doc['document_type']}\n"
                    doc_context += f"Publication Date: {doc['publication_date']}\n"
                    doc_context += f"Abstract: {self._clean_text(doc['abstract'])}\n"
            else:
                if is_recent_query:
                    doc_context = "\nNo recent documents found in the database.\n"
                else:
                    doc_context = "\nNo documents found matching the query.\n"
                logger.warning("No documents found in results")

            # Add specific instruction for recent document queries
            if is_recent_query:
                doc_context += "\nInstructions: Please list the documents in chronological order, starting with the most recent. Include the publication date for each document.\n"

            # Call Ollama API with document context
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": settings.MODEL_NAME,
                    "prompt": f"{self.system_prompt}\n\nContext:{doc_context}\n\nUser: {query}\nAssistant:",
                    "stream": False
                }
                
                async with session.post(settings.OLLAMA_API_URL, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Clean the response text
                        cleaned_response = self._clean_text(result.get('response', ''))
                        return {
                            'response': cleaned_response,
                            'success': True,
                            'documents_found': len(documents) > 0
                        }
                    else:
                        error_msg = f"Ollama API error: {response.status}"
                        logger.error(error_msg)
                        return {
                            'response': error_msg,
                            'success': False,
                            'documents_found': len(documents) > 0
                        }
                        
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            logger.error(error_msg)
            return {
                'response': error_msg,
                'success': False,
                'documents_found': False
            }

    def _clean_text(self, text: str) -> str:
        """Clean text to ensure only standard English characters are used."""
        if not text:
            return ""
        
        # Replace common problematic characters
        replacements = {
            '疾病': 'Disease',
            '控制': 'Control',
            '预防': 'Prevention',
            # Add more replacements as needed
        }
        
        cleaned = text
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
            
        # Remove any remaining non-ASCII characters
        cleaned = ''.join(char for char in cleaned if ord(char) < 128)
        return cleaned.strip() 