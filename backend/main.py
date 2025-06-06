import asyncio
import logging
from fastapi import FastAPI, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI

from pdf_loader import load_pdf_chunks_and_embeddings, get_relevant_chunks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app and set up CORS middleware
app = FastAPI()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI()

# Global variables to store PDF chunks and their embeddings
chunks = []
embeddings = []

# Load PDF data and embeddings when the application starts
@app.on_event("startup")
async def startup_event():
    """Load PDF chunks and their embeddings into memory on application startup."""
    global chunks, embeddings
    try:
        chunks, embeddings = await load_pdf_chunks_and_embeddings("TravelContext.pdf")
        logger.info(f"Successfully loaded {len(chunks)} chunks and their embeddings.")
    except Exception as e:
        logger.error(f"Failed to load PDF chunks: {str(e)}")
        raise

# Handle streaming of OpenAI responses
async def openai_stream(messages):
    """
    Stream responses from OpenAI's API with a natural typing delay.
    
    Args:
        messages: List of message objects for the chat completion
        
    Yields:
        str: Tokens from the AI response
    """
    def sync_stream():
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True
        )
        for chunk in response:
            content = getattr(chunk.choices[0].delta, "content", "")
            yield content or ""

    async def async_generator():
        for token in sync_stream():
            await asyncio.sleep(0.015)  # Simulate natural typing delay
            yield token

    return async_generator()

# Main chat endpoint that handles user messages and returns AI responses
@app.get("/chat")
async def chat_get(
    conversation_id: str = Query(...),
    message: str = Query(...)
):
    """
    Handle chat requests, retrieve relevant context, and stream AI responses.
    
    Args:
        conversation_id: Unique identifier for the conversation
        message: User's input message
        
    Returns:
        StreamingResponse: Server-sent events stream of AI response tokens
    """
    relevant_chunks = await get_relevant_chunks(message, chunks, embeddings, top_k=3)
    context_text = "\n\n".join(relevant_chunks)

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "system", "content": f"Use the following context from a PDF to help answer:\n{context_text}"},
        {"role": "user", "content": message},
    ]

    async def event_generator():
        async for token in await openai_stream(messages):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"  # Signal end of stream

    return StreamingResponse(event_generator(), media_type="text/event-stream")
