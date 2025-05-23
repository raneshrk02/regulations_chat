import aiohttp #type:ignore
import asyncio
import json
from datetime import datetime, timedelta
import logging
from ..core.config import get_settings
from ..core.database import init_db, get_db
import dateutil.parser  # Add this import

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_regulations_data(start_date: str, end_date: str) -> list:
    """Fetch data from Regulations.gov API for the given date range."""
    async with aiohttp.ClientSession() as session:
        params = {
            'filter[postedDate][ge]': start_date,
            'filter[postedDate][le]': end_date,
            'sort': '-postedDate',
            'page[size]': 250,
            'api_key': settings.REGULATIONS_API_KEY
        }
        
        try:
            documents = []
            page = 1
            while True:
                params['page[number]'] = page
                async with session.get(f"{settings.REGULATIONS_API_URL}/v4/documents", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data.get('data'):
                            break
                        documents.extend(data['data'])
                        page += 1
                        if page > 20:  # Limit to 5000 documents per fetch (20 pages * 250 per page)
                            break
                    else:
                        logger.error(f"Failed to fetch data: {response.status}")
                        break
            return documents
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return []

async def process_and_store_documents(documents: list):
    """Process and store documents in the database."""
    async with get_db() as cur:
        for doc in documents:
            try:
                # Extract relevant fields from the document attributes
                attributes = doc.get('attributes', {})
                
                # Parse the publication date
                posted_date = attributes.get('postedDate')
                if posted_date:
                    try:
                        publication_date = dateutil.parser.parse(posted_date)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid date format for document {doc.get('id')}: {posted_date}")
                        publication_date = None
                else:
                    publication_date = None
                
                doc_data = {
                    'id': doc.get('id'),
                    'title': attributes.get('title'),
                    'document_number': attributes.get('documentNumber'),
                    'document_type': attributes.get('documentType'),
                    'publication_date': publication_date,
                    'abstract': attributes.get('abstract'),
                    'full_text': attributes.get('fileText'),
                    'agencies': json.dumps([agency.get('name') for agency in attributes.get('agencies', [])])
                }
                
                # Skip if document ID is None
                if not doc_data['id']:
                    continue
                
                # Insert or update document
                query = """
                    INSERT INTO documents 
                    (id, title, document_number, document_type, publication_date, 
                     abstract, full_text, agencies) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    title=VALUES(title),
                    document_number=VALUES(document_number),
                    document_type=VALUES(document_type),
                    publication_date=VALUES(publication_date),
                    abstract=VALUES(abstract),
                    full_text=VALUES(full_text),
                    agencies=VALUES(agencies)
                """
                
                await cur.execute(query, (
                    doc_data['id'], doc_data['title'], doc_data['document_number'],
                    doc_data['document_type'], doc_data['publication_date'],
                    doc_data['abstract'], doc_data['full_text'], doc_data['agencies']
                ))
                
            except Exception as e:
                logger.error(f"Error processing document {doc.get('id')}: {str(e)}")

async def run_pipeline(days: int = 7):
    """Run the data pipeline to fetch and store Regulations.gov data.
    
    Args:
        days (int): Number of days to look back for documents. Defaults to 7.
    """
    try:
        # Initialize database
        await init_db()
        
        # Set date range
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        logger.info(f"Fetching data from {start_date} to {end_date}")
        
        # Fetch and process data
        documents = await fetch_regulations_data(start_date, end_date)
        if documents:
            logger.info(f"Found {len(documents)} documents")
            await process_and_store_documents(documents)
            logger.info("Data pipeline completed successfully")
        else:
            logger.warning("No documents found")
            
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")

if __name__ == "__main__":
    # Run for 120 days (approximately 4 months)
    asyncio.run(run_pipeline(120)) 