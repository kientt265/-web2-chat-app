"""
Service initialization utilities

Helper functions to ensure services are properly initialized
when agents are used outside of the FastAPI application context.
"""

import logging
from services.chromadb_service import chromadb_service

logger = logging.getLogger(__name__)


async def ensure_chromadb_initialized() -> bool:
    """
    Ensure ChromaDB service is initialized.
    Returns True if successful, False otherwise.
    """
    try:
        # Check if already initialized
        if chromadb_service.collection is not None:
            logger.info("ChromaDB already initialized")
            return True

        # Try to initialize
        logger.info("Initializing ChromaDB service...")
        success = await chromadb_service.initialize()

        if success:
            logger.info("✅ ChromaDB service initialized successfully")
            return True
        else:
            logger.warning("❌ ChromaDB service initialization failed")
            return False

    except Exception as e:
        logger.error(f"❌ Error initializing ChromaDB service: {e}")
        return False


async def get_service_status() -> dict:
    """Get the status of all services"""
    status = {"chromadb": {"available": False, "initialized": False, "error": None}}

    try:
        # Check ChromaDB availability
        if chromadb_service:
            status["chromadb"]["available"] = True

            # Check if initialized
            if chromadb_service.collection:
                status["chromadb"]["initialized"] = True

                # Try to get stats to confirm it's working
                try:
                    stats = await chromadb_service.get_stats()
                    status["chromadb"]["stats"] = stats
                except Exception as e:
                    status["chromadb"]["error"] = str(e)
            else:
                # Try to initialize
                try:
                    await ensure_chromadb_initialized()
                    status["chromadb"]["initialized"] = (
                        chromadb_service.collection is not None
                    )
                except Exception as e:
                    status["chromadb"]["error"] = str(e)

    except Exception as e:
        status["chromadb"]["error"] = str(e)

    return status
