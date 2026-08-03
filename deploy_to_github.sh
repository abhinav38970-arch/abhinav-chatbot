#!/bin/bash
# TASK 5: GITHUB DEPLOYMENT SCRIPT
# Git commands to commit changes and push to deployment-ready branch

echo "🚀 Starting GitHub Deployment to deployment-ready branch"
echo "======================================================"

# Add all modified files
echo "📝 Adding modified files..."
git add backend/app/retrieval/search.py
git add backend/app/scraper/crawler.py
git add backend/app/scraper/parser.py
git add backend/app/scraper/pdf_handler.py
git add backend/app/services/search_service.py

# Add the new reset script
echo "📝 Adding new reset_and_rebuild.py script..."
git add reset_and_rebuild.py

# Commit with a descriptive message
echo "💾 Committing changes..."
git commit -m "Demo-Ready Sprint: Implement all 5 critical tasks for WHS District Meeting

- TASK 1: GREETING & INTENT ROUTER - Detect casual greetings and return professional welcome
- TASK 2: ADVANCED DATA SCRAPING - HTML tables → Markdown, PDF tables via pdfplumber, image alt text extraction
- TASK 3: STRICT DOMAIN ISOLATION - Only fremontunified.org/washington/* and general district pages, exclude all other schools
- TASK 3: RECENCY FILTERING - Metadata tagging with scrape_date, prioritize recent documents
- TASK 4: DATABASE INGESTION - reset_and_rebuild.py script to clear old data and ingest fresh Washington HS data
- TASK 5: GITHUB DEPLOYMENT - This commit prepares for Streamlit Cloud demo deployment"

# Push to deployment-ready branch
echo "🌐 Pushing to deployment-ready branch..."
git push origin deployment-ready

echo "✅ Deployment complete!"
echo "🎯 Streamlit Cloud will automatically update for the demo"
echo "📅 Ready for Wednesday 2:00 PM district meeting presentation"