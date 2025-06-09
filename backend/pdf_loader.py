import json
import os
import logging
import numpy as np
from typing import List, Tuple, Optional
from fastapi.concurrency import run_in_threadpool
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from a PDF file using PyPDF2.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        str: Extracted text content
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        Exception: For any other extraction errors
    """
    from PyPDF2 import PdfReader
    
    try:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")
            
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
            
        if not text.strip():
            logger.warning(f"No text could be extracted from {pdf_path}")
            
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
        raise

def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text to split
        chunk_size: Maximum size of each chunk
        chunk_overlap: Number of characters to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    if not text:
        logger.warning("Empty text provided for splitting")
        return []
        
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
        
    logger.debug(f"Split text into {len(chunks)} chunks")
    return chunks

async def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of text chunks using OpenAI's API.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List[List[float]]: List of embedding vectors
        
    Raises:
        Exception: If embedding generation fails
    """
    if not texts:
        logger.warning("No texts provided for embedding")
        return []
        
    try:
        embeddings = []
        logger.info(f"Generating embeddings for {len(texts)} text chunks...")
        
        for text in texts:
            response = await run_in_threadpool(
                lambda: client.embeddings.create(
                    model="text-embedding-3-large",
                    input=text,
                )
            )
            embeddings.append(response.data[0].embedding)
            
        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise

def save_embeddings(filepath: str, chunks: List[str], embeddings: List[List[float]]) -> None:
    """
    Save text chunks and their embeddings to a JSON file.
    
    Args:
        filepath: Path to save the embeddings
        chunks: List of text chunks
        embeddings: List of corresponding embedding vectors
        
    Raises:
        IOError: If there's an error writing to the file
    """
    try:
        to_save = [{"text": chunk, "embedding": emb} for chunk, emb in zip(chunks, embeddings)]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(to_save, f)
        logger.info(f"Saved {len(chunks)} chunks and embeddings to {filepath}")
    except IOError as e:
        logger.error(f"Error saving embeddings to {filepath}: {str(e)}")
        raise

def load_embeddings(filepath: str) -> Tuple[Optional[List[str]], Optional[List[List[float]]]]:
    """
    Load text chunks and their embeddings from a JSON file.
    
    Args:
        filepath: Path to the embeddings file
        
    Returns:
        Tuple containing:
            - List of text chunks (or None if not found)
            - List of embedding vectors (or None if not found)
    """
    if not os.path.exists(filepath):
        logger.warning(f"Embeddings file not found at {filepath}")
        return None, None
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        chunks = [item["text"] for item in data]
        embeddings = [item["embedding"] for item in data]
        
        logger.info(f"Loaded {len(chunks)} chunks and embeddings from {filepath}")
        return chunks, embeddings
        
    except (json.JSONDecodeError, KeyError, IOError) as e:
        logger.error(f"Error loading embeddings from {filepath}: {str(e)}")
        return None, None

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        float: Cosine similarity score between -1 and 1
    """
    try:
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {str(e)}")
        return 0.0

async def get_relevant_chunks(
    query: str, 
    chunks: List[str], 
    embeddings: List[List[float]], 
    top_k: int = 5
) -> List[str]:
    """
    Find the most relevant text chunks for a given query using semantic search.
    
    Args:
        query: Search query
        chunks: List of text chunks to search through
        embeddings: Corresponding embeddings for the chunks
        top_k: Number of top results to return
        
    Returns:
        List[str]: Top-k most relevant text chunks
    """
    if not chunks or not embeddings:
        logger.warning("No chunks or embeddings provided for search")
        return []
        
    try:
        logger.debug(f"Finding relevant chunks for query: {query[:100]}...")
        query_emb_list = await embed_texts([query])
        query_emb = query_emb_list[0]
        
        scores = [cosine_similarity(np.array(query_emb), np.array(emb)) for emb in embeddings]
        ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Top result score: {ranked[0][1]:.3f} (query: {query[:50]}...)")
        return [chunk for chunk, score in ranked[:top_k]]
        
    except Exception as e:
        logger.error(f"Error finding relevant chunks: {str(e)}")
        return []

async def load_pdf_chunks_and_embeddings(
    pdf_path: str, 
    embeddings_path: str = "pdf_embeddings.json"
) -> Tuple[List[str], List[List[float]]]:
    """
    Load or generate PDF chunks and their embeddings.
    
    Args:
        pdf_path: Path to the PDF file
        embeddings_path: Path to save/load embeddings
        
    Returns:
        Tuple containing:
            - List of text chunks
            - List of corresponding embedding vectors
    """
    # Try to load cached embeddings first
    chunks, embeddings = load_embeddings(embeddings_path)
    if chunks is not None and embeddings is not None:
        logger.info(f"Using cached embeddings from {embeddings_path}")
        return chunks, embeddings

    # If no cache, process the PDF
    logger.info(f"Processing PDF: {pdf_path}")
    try:
        text = extract_text_from_pdf(pdf_path)
        logger.info(f"Extracted {len(text)} characters from PDF")
        
        chunks = split_text(text)
        logger.info(f"Split PDF into {len(chunks)} chunks")
        
        embeddings = await embed_texts(chunks)
        
        # Save the embeddings for future use
        save_embeddings(embeddings_path, chunks, embeddings)
        
        return chunks, embeddings
        
    except Exception as e:
        logger.error(f"Failed to process PDF {pdf_path}: {str(e)}")
        raise
