# backend/app/retrieval/chunker.py
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
import re
from typing import List, Dict

def smart_chunk_text(text: str, chunk_size: int = 600, overlap: int = 100, content_type: str = "text") -> List[Dict]:
    """
    Enhanced smart chunking with semantic awareness and metadata preservation.
    
    Features:
    - Content-type aware (markdown, html, text)
    - Preserves headers and structure
    - Adds semantic metadata
    - Maintains context across chunks
    """
    if not text or len(text.strip()) == 0:
        return []
    
    # Initialize enhanced chunker with better separators
    base_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n\n", "\n\n", "\n", ". ", "! ", "? ", " ", ""],
        length_function=len
    )
    
    chunks = []
    
    # Content-type specific handling
    if content_type == "markdown":
        # Try to preserve markdown structure
        try:
            headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3")
            ]
            
            markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on,
                strip_headers=False
            )
            
            # Split by headers first, then chunk each section
            md_sections = markdown_splitter.split_text(text)
            for section in md_sections:
                section_text = section.page_content
                section_chunks = base_splitter.split_text(section_text)
                
                for chunk in section_chunks:
                    chunks.append({
                        "content": chunk,
                        "metadata": {
                            "content_type": "markdown",
                            "header": section.metadata.get("Header 1", ""),
                            "section": section.metadata.get("Header 2", ""),
                            "subsection": section.metadata.get("Header 3", ""),
                            "semantic_role": "structured_content"
                        }
                    })
            
            return chunks if chunks else [{"content": text, "metadata": {"content_type": "markdown", "semantic_role": "full_document"}}]
            
        except Exception:
            # Fallback to basic splitting
            pass
    
    # For HTML content, try to preserve table structures
    if content_type == "html":
        # Detect and preserve tables
        table_pattern = r'<table>.*?</table>'
        tables = re.findall(table_pattern, text, re.DOTALL)
        
        if tables:
            # Process non-table content
            text_without_tables = re.sub(table_pattern, ' [TABLE_PLACEHOLDER] ', text, flags=re.DOTALL)
            text_chunks = base_splitter.split_text(text_without_tables)
            
            # Add table chunks separately
            for i, table in enumerate(tables):
                chunks.append({
                    "content": table,
                    "metadata": {
                        "content_type": "html_table",
                        "table_id": f"table_{i+1}",
                        "semantic_role": "tabular_data",
                        "preserve_format": True
                    }
                })
            
            # Add text chunks
            for chunk in text_chunks:
                chunks.append({
                    "content": chunk,
                    "metadata": {
                        "content_type": "html_text",
                        "semantic_role": "narrative_content"
                    }
                })
            
            return chunks if chunks else [{"content": text, "metadata": {"content_type": "html", "semantic_role": "full_document"}}]
    
    # Default text processing with enhanced metadata
    text_chunks = base_splitter.split_text(text)
    
    for i, chunk in enumerate(text_chunks):
        # Add semantic analysis
        semantic_role = "unknown"
        
        # Simple heuristic for semantic role detection
        if re.search(r'\b(schedule|time|period|bell)\b', chunk, re.IGNORECASE):
            semantic_role = "schedule_info"
        elif re.search(r'\b(policy|rule|procedure|guideline)\b', chunk, re.IGNORECASE):
            semantic_role = "policy_info"
        elif re.search(r'\b(event|activity|meeting|conference)\b', chunk, re.IGNORECASE):
            semantic_role = "event_info"
        elif re.search(r'\b(contact|email|phone|staff)\b', chunk, re.IGNORECASE):
            semantic_role = "contact_info"
        
        chunks.append({
            "content": chunk,
            "metadata": {
                "content_type": "text",
                "semantic_role": semantic_role,
                "chunk_index": i,
                "total_chunks": len(text_chunks)
            }
        })
    
    return chunks if chunks else [{"content": text, "metadata": {"content_type": "text", "semantic_role": "full_document"}}]

def chunk_text(text, chunk_size=600, overlap=100):
    """
    Backward-compatible wrapper for existing code
    """
    result = smart_chunk_text(text, chunk_size, overlap)
    # Return just the text for backward compatibility
    return [chunk["content"] for chunk in result] if isinstance(result, list) else [result["content"]] if result else []