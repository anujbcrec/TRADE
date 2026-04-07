"""
Database initialization script to create indexes for optimal query performance.
Run this once during deployment or app startup.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_indexes():
    """Create necessary database indexes."""
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    
    try:
        await db.trades.create_index([("timestamp", -1)])
        logger.info("✓ Created index on trades.timestamp")
        
        await db.trades.create_index([("symbol", 1)])
        logger.info("✓ Created index on trades.symbol")
        
        await db.positions.create_index([("symbol", 1)])
        logger.info("✓ Created index on positions.symbol")
        
        await db.positions.create_index([("opened_at", -1)])
        logger.info("✓ Created index on positions.opened_at")
        
        logger.info("Database indexes created successfully!")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_indexes())
