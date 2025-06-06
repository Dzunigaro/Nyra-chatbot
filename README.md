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

2. Backend Setup (Python / FastAPI)
Create a virtual environment:
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
Create a .env file based on .env.example:
cp .env.example .env
Update it with your actual API key(s).

Run the backend:
uvicorn main:app --reload --port 8000

3. Frontend Setup (React / Vite)
cd frontend  # if frontend is in a subfolder; otherwise, skip
npm install
npm run dev
This will launch the React app at http://localhost:5173 (or the port Vite chooses).

🔧 Configuration
.env file (Backend):
OPENAI_API_KEY=your_openai_key