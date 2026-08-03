#!/usr/bin/env python3
"""
TASK 4: DATABASE INGESTION & FRESH CRAWL
Script to clear old FAISS vector database and ingest fresh Washington High School data
"""

import os
import shutil
from backend.app.scraper.pipeline import run_pipeline
from backend.app.retrieval.indexer import build_index
from backend.app.retrieval.vector_store import VectorStore
from backend.app.retrieval.embedder import embed_text
import numpy as np

def clear_old_database():
    """Clear the old FAISS vector database and metadata"""
    print("🧹 Clearing old vector database...")
    
    # Remove FAISS index file
    index_path = "backend/app/retrieval/faiss.index"
    if os.path.exists(index_path):
        os.remove(index_path)
        print(f"✅ Removed {index_path}")
    
    # Remove metadata file
    meta_path = "backend/app/retrieval/meta.pkl"
    if os.path.exists(meta_path):
        os.remove(meta_path)
        print(f"✅ Removed {meta_path}")
    
    # Clear SQLite database
    db_path = "backend/app/database/pages.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✅ Removed {db_path}")

def run_fresh_crawl():
    """Run the scraper with new advanced parsing capabilities"""
    print("🕷️  Running fresh crawl with advanced scraping...")
    run_pipeline()
    print("✅ Crawl completed")

def rebuild_vector_index():
    """Rebuild the vector index with recency metadata"""
    print("🔧 Rebuilding vector index with recency filtering...")
    build_index()
    print("✅ Vector index rebuilt")

def main():
    print("🚀 Starting Demo-Ready Database Reset & Rebuild")
    print("=" * 60)
    
    try:
        # Step 1: Clear old data
        clear_old_database()
        
        # Step 2: Run fresh crawl with advanced features
        run_fresh_crawl()
        
        # Step 3: Rebuild vector index
        rebuild_vector_index()
        
        print("\n🎉 Database reset and rebuild completed successfully!")
        print("✨ Your AI pipeline is now demo-ready with:")
        print("   - Strict domain isolation (Washington HS only)")
        print("   - Advanced table and PDF parsing")
        print("   - Recency-based result prioritization")
        print("   - Professional greeting handling")
        
    except Exception as e:
        print(f"❌ Error during rebuild: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())