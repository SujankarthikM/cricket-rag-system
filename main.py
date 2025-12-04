#!/usr/bin/env python3
"""
Cricket RAG System - FastAPI Server
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import time
from pathlib import Path
import tempfile
import shutil
import sqlite3

from rag_system.data_ingestion import DataIngestion
from rag_system.vector_store import VectorStore

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class QueryResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    processing_time_ms: float

class StatsResponse(BaseModel):
    total_documents: int
    collection_name: str
    embedding_model: str

class UploadResponse(BaseModel):
    success: bool
    message: str
    documents_added: int

# Initialize FastAPI app
app = FastAPI(
    title="Cricket RAG API",
    description="RAG system for cricket-related content with page/index tracking",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
data_ingestion = DataIngestion()
vector_store = VectorStore()

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint"""
    return {
        "message": "Cricket RAG API is running!",
        "version": "1.0.0",
        "endpoints": ["/search", "/context/{document_id}", "/stats", "/upload", "/ingest", "/health"]
    }

@app.post("/search", response_model=QueryResponse)
async def search(request: QueryRequest):
    """Search for documents similar to the query"""
    start_time = time.time()
    
    try:
        results = vector_store.search(request.query, request.top_k)
        processing_time = (time.time() - start_time) * 1000
        
        return QueryResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            processing_time_ms=round(processing_time, 2)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/context/{document_id}", response_model=Dict[str, Any])
async def get_context(document_id: str):
    """Get full context for a document using its original_document_id"""
    try:
        context = vector_store.get_full_context(document_id)
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get vector store statistics"""
    try:
        stats = data_ingestion.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a new file"""
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ['.pdf', '.json']:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_extension}. Only PDF and JSON files are supported."
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = Path(tmp_file.name)
        
        try:
            # Process the file
            result = data_ingestion.add_single_file(tmp_path)
            
            if result["success"]:
                return UploadResponse(
                    success=True,
                    message=f"Successfully processed {file.filename}",
                    documents_added=result["documents_added"]
                )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to process file: {result['error']}"
                )
        
        finally:
            # Clean up temporary file
            tmp_path.unlink(missing_ok=True)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/ingest")
async def ingest_all_data(reset_db: bool = False):
    """Ingest all available data files from data_for_rag directory"""
    try:
        stats = data_ingestion.ingest_all_data(reset_db=reset_db)
        return {
            "message": "Data ingestion completed",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        stats = data_ingestion.get_stats()
        return {
            "status": "healthy",
            "total_documents": stats["total_documents"],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }

if __name__ == "__main__":
    print("🏏 Starting Cricket RAG FastAPI Server...")
    print("📡 API will be available at: http://localhost:8000")
    print("📖 Interactive docs at: http://localhost:8000/docs")
    print("🔍 Endpoints:")
    print("  - POST /search           : Search documents")
    print("  - GET  /context/{doc_id} : Get full context")
    print("  - GET  /stats            : Get statistics")
    print("  - POST /upload           : Upload new files")
    print("  - POST /ingest           : Ingest all data")
    print("  - GET  /health           : Health check")
    
    uvicorn.run(
        "__main__:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )