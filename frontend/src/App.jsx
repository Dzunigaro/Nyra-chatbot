import React, { useState, useRef, useEffect, useCallback } from "react";
import "./App.css";
import { v4 as uuidv4 } from "uuid";

/**
 * Main App component that handles the chat interface
 * Manages conversations, messages, and real-time updates
 */
export default function App() {
  // State management for messages, input, and UI states
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);
  
  // Conversations state and active conversation ID
  const [conversations, setConversations] = useState(() => {
    // Load conversations from localStorage or initialize empty object
    return JSON.parse(localStorage.getItem("conversations") || "{}");
  });
  const [conversationId, setConversationId] = useState("");

  // Refs for DOM access and event source management
  const eventSourceRef = useRef(null);
  const chatBoxRef = useRef(null);

  /**
   * Creates a new conversation with a unique ID
   * Updates both state and localStorage
   */
  const startNewConversation = useCallback(() => {
    const newId = uuidv4();
    const updated = { ...conversations, [newId]: [] };
    localStorage.setItem("conversations", JSON.stringify(updated));
    localStorage.setItem("activeConversation", newId);
    setConversations(updated);
    setConversationId(newId);
    setMessages([]);
  }, [conversations]);

  // Set active conversation on component mount or conversation change
  useEffect(() => {
    const saved = localStorage.getItem("activeConversation");
    if (saved && conversations[saved]) {
      setConversationId(saved);
    } else {
      startNewConversation();
    }
  }, [conversations, startNewConversation]);

  // Update messages when conversation changes
  useEffect(() => {
    if (conversationId) {
      const existingMessages = conversations[conversationId] || [];
      setMessages(existingMessages);
    }
  }, [conversationId, conversations]);

  // Auto-scroll to bottom when messages or typing states change
  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages, isTyping, isWaiting]);

  /**
   * Sends a message to the server and handles the streaming response
   * Manages the chat state, typing indicators, and message updates
   */
  const sendMessage = () => {
    if (!input.trim()) return;

    // Create and add user message to the conversation
    const userMessage = { sender: "user", text: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    updateConversation(conversationId, newMessages);
    setInput("");
    
    // Set UI states for loading
    setIsTyping(true);
    setIsWaiting(true);

    // Create a new EventSource for server-sent events
    eventSourceRef.current = new EventSource(
      `http://127.0.0.1:8000/chat?conversation_id=${conversationId}&message=${encodeURIComponent(input)}`
    );

    let isFirstChunk = true;

    // Handle incoming message chunks from the server
    eventSourceRef.current.onmessage = (e) => {
      if (e.data === "[DONE]") {
        // Clean up when streaming is complete
        setIsTyping(false);
        setIsWaiting(false);
        eventSourceRef.current?.close();
        eventSourceRef.current = null;

        // Save final messages after stream ends
        setMessages((finalMessages) => {
          const updatedConvos = { ...conversations, [conversationId]: finalMessages };
          localStorage.setItem("conversations", JSON.stringify(updatedConvos));
          setConversations(updatedConvos);
          return finalMessages;
        });
      } else {
        const chunk = e.data;

        if (isFirstChunk) {
          // Hide thinking indicator and create initial AI message with first chunk
          setIsWaiting(false);
          setMessages((prev) => [...prev, { sender: "ai", text: chunk }]);
          isFirstChunk = false;
        } else {
          // Update the existing AI message with new chunks
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.sender === "ai") {
              updated[updated.length - 1] = { ...last, text: (last.text || "") + chunk };

              // Update conversations in state and localStorage
              setConversations((prevConvos) => {
                const updatedConvos = { ...prevConvos };
                if (!updatedConvos[conversationId]) {
                  updatedConvos[conversationId] = [];
                }
                updatedConvos[conversationId] = updated;
                localStorage.setItem("conversations", JSON.stringify(updatedConvos));
                return updatedConvos;
              });
            }
            return updated;
          });
        }
      }
    };

    // Handle any errors with the event source
    eventSourceRef.current.onerror = () => {
      console.error("SSE error");
      setIsTyping(false);
      setIsWaiting(false);
      eventSourceRef.current?.close();
      eventSourceRef.current = null;
    };
  };

  /**
   * Updates a conversation in both state and localStorage
   * @param {string} id - Conversation ID
   * @param {Array} msgs - Array of messages in the conversation
   */
  const updateConversation = (id, msgs) => {
    const updated = { ...conversations, [id]: msgs };
    setConversations(updated);
    localStorage.setItem("conversations", JSON.stringify(updated));
  };

  /**
   * Clears all messages in the current conversation
   */
  const clearChat = () => {
    const updated = { ...conversations, [conversationId]: [] };
    setMessages([]);
    setConversations(updated);
    localStorage.setItem("conversations", JSON.stringify(updated));
  };

  /**
   * Generates a title for a conversation based on the first user message
   * @param {string} id - Conversation ID
   * @returns {string} Generated title or "New Chat"
   */
  const getChatTitle = (id) => {
    const convo = conversations[id];
    if (!Array.isArray(convo) || convo.length === 0) return "New Chat";
    const firstUserMsg = convo.find((msg) => msg.sender === "user");
    return firstUserMsg?.text?.slice(0, 20) || "New Chat";
  };

  // Render the chat interface
  return (
    <div className="app-container">
      {/* Sidebar with conversation list */}
      <div className="sidebar">
        <button className="new-chat-btn" onClick={startNewConversation}>
          + New Chat
        </button>
        <ul className="conversation-list">
          {Object.keys(conversations).map((id) => (
            <li
              key={id}
              className={id === conversationId ? "active" : ""}
              onClick={() => {
                if (!isTyping) setConversationId(id);
              }}
            >
              {getChatTitle(id)}
            </li>
          ))}
        </ul>
      </div>

      {/* Main chat area */}
      <div className="chat-container">
        <h1 className="title">🤖 Nyra</h1>
        <div className="chat-box" ref={chatBoxRef}>
          {/* Render all messages */}
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`message ${msg.sender === "user" ? "user" : "ai"}`}
            >
              {msg.text}
              {/* Show typing cursor on the last AI message when typing */}
              {isTyping && msg.sender === "ai" && idx === messages.length - 1 && (
                <span className="blinking-cursor">|</span>
              )}
            </div>
          ))}
          {/* Show thinking indicator when waiting for response */}
          {isWaiting && <div className="typing waiting">Nyra is thinking</div>}
        </div>

        {/* Message input area */}
        <div className="input-row">
          <input
            type="text"
            className="chat-input"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            disabled={isTyping}
          />
          <button
            className="send-btn"
            onClick={sendMessage}
            disabled={!input.trim() || isTyping}
          >
            Send
          </button>
          <button className="clear-btn" onClick={clearChat} disabled={isTyping}>
            Clear
          </button>
        </div>
      </div>
    </div>
  );
}