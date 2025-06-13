# Updated and personalized version of app.py for TDS Virtual TA
# Author: Siddarth S. (Customized for final submission)

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
import traceback
import logging
import os
from utils.embedding_handler import process_multimodal_query
from utils.similarity_search import find_similar_content, enrich_with_adjacent_chunks
from utils.llm_interface import generate_answer, parse_llm_response

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend testing or usage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TDS-VTA")

# Load environment variable
API_KEY = os.getenv("API_KEY")
DB_PATH = "knowledge_base.db"

class QueryRequest(BaseModel):
    question: str
    image: UploadFile | None = None

@app.post("/query")
async def query_knowledge_base(request: QueryRequest):
    try:
        conn = sqlite3.connect(DB_PATH)

        try:
            logger.info("➡️ Starting query processing")
            
            embedding = await process_multimodal_query(request.question, request.image)
            logger.info("✅ Embedding generated")

            similar_results = await find_similar_content(embedding, conn)
            if not similar_results:
                return {"answer": "No relevant info found.", "links": []}

            enriched = await enrich_with_adjacent_chunks(conn, similar_results)
            response = await generate_answer(request.question, enriched)
            result = parse_llm_response(response)

            if not result.get("links"):
                seen_urls = set()
                result["links"] = []
                for entry in similar_results[:5]:
                    if entry["url"] not in seen_urls:
                        seen_urls.add(entry["url"])
                        snippet = entry["content"][:100] + "..."
                        result["links"].append({"url": entry["url"], "text": snippet})

            logger.info(f"✅ Query complete: Answer length={len(result['answer'])}, Links={len(result['links'])}")
            return result

        except Exception as inner_err:
            logger.error("❌ Error inside query block")
            logger.error(traceback.format_exc())
            return JSONResponse(status_code=500, content={"error": str(inner_err)})

        finally:
            conn.close()

    except Exception as outer_err:
        logger.error("❌ Unhandled exception in /query")
        logger.error(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(outer_err)})

@app.get("/health")
async def health_check():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM discourse_chunks")
        disc_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM markdown_chunks")
        mark_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM discourse_chunks WHERE embedding IS NOT NULL")
        disc_embed = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM markdown_chunks WHERE embedding IS NOT NULL")
        mark_embed = cursor.fetchone()[0]

        conn.close()

        return {
            "status": "healthy",
            "db": "connected",
            "api_key_present": bool(API_KEY),
            "discourse_count": disc_count,
            "markdown_count": mark_count,
            "discourse_embeddings": disc_embed,
            "markdown_embeddings": mark_embed
        }

    except Exception as err:
        logger.error("❌ Health check failed")
        return JSONResponse(status_code=500, content={"status": "unhealthy", "error": str(err)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
