import aiomysql #type:ignore
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from .config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

async def init_db():
    """Initialize the database and create tables if they don't exist."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Drop existing documents table
            await cur.execute("DROP TABLE IF EXISTS documents")
            await conn.commit()
            
            # Create documents table
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id VARCHAR(255) PRIMARY KEY,
                    title TEXT,
                    document_number VARCHAR(255),
                    document_type VARCHAR(100),
                    publication_date DATETIME,
                    abstract TEXT,
                    full_text TEXT,
                    agencies TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FULLTEXT KEY doc_search_idx (title, abstract, full_text)
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            await conn.commit()

async def get_db_pool():
    """Get a connection pool to the database."""
    return await aiomysql.create_pool(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        db=settings.MYSQL_DATABASE,
        charset='utf8mb4',
        cursorclass=aiomysql.cursors.DictCursor,
        autocommit=True
    )

@asynccontextmanager
async def get_db() -> AsyncGenerator:
    """Get a database connection from the pool."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            yield cur

async def close_db_connection(pool: aiomysql.Pool):
    """Close the database connection pool."""
    pool.close()
    await pool.wait_closed()

async def get_recent_documents(limit: int = 10):
    """Get the most recently added documents from the database.
    
    Args:
        limit (int): Maximum number of documents to return. Defaults to 10.
        
    Returns:
        List of dictionaries containing document information sorted by creation date.
    """
    async with get_db() as cur:
        await cur.execute("""
            SELECT 
                id,
                title,
                document_number,
                document_type,
                publication_date,
                abstract,
                agencies,
                created_at
            FROM documents 
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        return await cur.fetchall()

async def test_db_connection():
    """Test database connection and count documents."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) as count FROM documents")
                result = await cur.fetchone()
                doc_count = result[0] if result else 0
                logger.info(f"Successfully connected to database. Found {doc_count} documents.")
                return True, doc_count
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return False, 0 