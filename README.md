# 🤖 Nyra Chatbot

Nyra is a web-based chat assistant powered by FastAPI and React. It supports streaming responses using Server-Sent Events (SSE) and persists chat history locally using `localStorage`. You can also embed PDF context for more intelligent, context-aware conversations.

---

## 🚀 Features

- React frontend with SSE support
- FastAPI backend with OpenAI (or Anthropic) integration
- PDF embedding and context-aware answers
- Persistent chat history (localStorage)
- Multiple chat sessions with titles
- Clean, dark-themed UI

---

## 🧱 Tech Stack

- Frontend: React + Vite
- Backend: FastAPI (Python)
- Embeddings: OpenAI API
- PDF parsing: PyMuPDF
- State persistence: localStorage

---

## 📦 Installation

### 1. Clone the Repo

```bash
git clone https://github.com/your-username/nyra-chatbot.git
cd nyra-chatbot
```

### 2. Backend Setup (Python / FastAPI)
```Create a virtual environment:
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```
```Install dependencies:
pip install -r requirements.txt
```
```Create a .env file based on .env.example:
cp .env.example .env
Update it with your actual API key(s).
```

```Run the backend:
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup (React / Vite)
```
cd frontend  # if frontend is in a subfolder; otherwise, skip
npm install
npm run dev
```
This will launch the React app at http://localhost:5173 (or the port Vite chooses).

---

## 🔧 Configuration
```.env file (Backend):
OPENAI_API_KEY=your_openai_key
```

---

## Challenges and Things Learned 

### Challenges:
1. Typing Indicator for Streaming Responses:
   - Tried implementing a "typing..." animation or effect as the response streams in, had a bit of trouble to get it working succesfully but in the end it worked.

2. Delete Conversation Functionality
   - Attempted to allow deleting past conversations from the sidebar, but the delete logic/UI wasn’t fully implemented or connected.
3. Add Export Option
   - Had a lot of of trouble trying to implement this and my code did not function at all when attempting this had to go back to past verions
4. Issues with Markdown
   - attempted to use markdown but with help created a differnet approach to extract chunks, embed and find accurate chunks based on question
5. System Prompt Configurator
   - Attempted to add UI option to the bots behavior became to complicated and decided to keep things simple

### Things learned:
1. Setting up FastAPI with CORS
  - I learned how to configure CORS middleware to allow secure communication between my frontend and backend.

2. Server-Sent Events (SSE) with FastAPI
  - I successfully implemented SSE to stream responses from the backend to the frontend using EventSource.

3. Integrating OpenAI API with Streaming
  - I figured out how to call the OpenAI API with streaming enabled and forward that stream to the client in real-time.

4. Building a Custom PDF Embedding Pipeline
   -I replaced LangChain and Markdown with my own approach using PyMuPDF:
     - Loaded PDF files.
     - Extracted and cleaned the text.
     - Chunked the content.
     - Embedded each chunk using OpenAI embeddings.
     - Performed similarity searches to retrieve relevant context.

5. Creating Context-Aware Chat Prompts
  - I implemented logic to retrieve relevant chunks from the PDF and inject them into chat prompts for more informed assistant responses.

6. Using React with Vite + JSX
  - I built a fast, clean frontend using React and Vite, which made development more efficient with hot reloading.

7. Streaming UI Updates with SSE
  - I connected to my FastAPI backend using EventSource and streamed assistant messages live into the chat interface.

8. Persistent Chat with localStorage
  - I implemented persistent conversation history using localStorage, including:
    - Loading saved conversations on startup.
    - Saving new messages per chat.
    - Starting new conversations cleanly.

9. State Management with Hooks
  - I used React hooks like useState, useEffect, and useRef to manage dynamic state and make the app responsive to user input and streaming events.
