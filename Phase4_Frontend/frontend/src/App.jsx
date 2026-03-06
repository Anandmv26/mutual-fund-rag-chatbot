import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import { WalletCards, Send, User, Bot, Sparkles, Code, Activity, Star, Info, ChevronDown, ChevronUp } from 'lucide-react'

// API endpoint configurable via env
const API_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? "http://localhost:8000" : "/api")

export default function App() {
    const [messages, setMessages] = useState([
        {
            id: "welcome",
            type: "bot",
            text: "Welcome to your premium investment suite. I am your specialized Mutual Fund advisor. How can I assist with your portfolio or market analysis today?",
            verified: true
        }
    ])
    const [suggestions, setSuggestions] = useState([
        "Best ELSS for tax saving",
        "Compare Large Cap vs Mid Cap",
        "Current market outlook"
    ])
    const [input, setInput] = useState("")
    const [loading, setLoading] = useState(false)
    const [supportedFunds, setSupportedFunds] = useState([])
    const [showFunds, setShowFunds] = useState(false)
    const chatEndRef = useRef(null)

    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    // Initial load to get trending suggestions and supported funds
    useEffect(() => {
        axios.get(`${API_URL}/suggestions`)
            .then(res => {
                if (res.data && res.data.suggestions) {
                    setSuggestions(res.data.suggestions)
                }
            })
            .catch(console.error)

        axios.get(`${API_URL}/supported-funds`)
            .then(res => {
                if (res.data && res.data.funds) {
                    setSupportedFunds(res.data.funds)
                }
            })
            .catch(console.error)
    }, [])

    const sendMessage = async (text) => {
        if (!text.trim()) return

        const userMessage = { id: Date.now().toString(), type: "user", text }
        setMessages(prev => [...prev, userMessage])
        setInput("")
        setLoading(true)

        try {
            const response = await axios.post(`${API_URL}/chat`, { message: text })
            const { answer, source_url, suggestions: newSug, is_in_scope } = response.data

            const botMessage = {
                id: (Date.now() + 1).toString(),
                type: "bot",
                text: answer,
                source: source_url,
                verified: is_in_scope
            }
            setMessages(prev => [...prev, botMessage])
            if (newSug && newSug.length > 0) setSuggestions(newSug)
        } catch (error) {
            const errorMessage = {
                id: (Date.now() + 1).toString(),
                type: "bot",
                text: "I encountered an error connecting to the secure servers. Please try again later.",
                verified: false
            }
            setMessages(prev => [...prev, errorMessage])
        } finally {
            setLoading(false)
        }
    }

    const handleSuggestionClick = (sug) => {
        sendMessage(sug)
    }

    const renderIcon = (idx) => {
        if (idx === 0) return <Bot size={16} />
        if (idx === 1) return <Code size={16} />
        return <Activity size={16} />
    }

    return (
        <div className="app-container">
            {/* Header */}
            <div className="header">
                <div className="header-icon">
                    <WalletCards size={24} color="#000" />
                </div>
                <h1>WealthWise AI</h1>
                <p>Your Gateway to Institutional-Grade Financial Growth</p>

                {supportedFunds.length > 0 && (
                    <div className="supported-funds-wrapper">
                        <button
                            className="supported-funds-toggle"
                            onClick={() => setShowFunds(!showFunds)}
                        >
                            <Info size={14} />
                            <span>Supported Mutual Funds</span>
                            {showFunds ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        </button>
                        {showFunds && (
                            <div className="supported-funds-list">
                                <ul>
                                    {supportedFunds.map((fund, idx) => (
                                        <li key={idx} onClick={() => {
                                            setInput(`Tell me about ${fund}`)
                                            setShowFunds(false)
                                        }}>
                                            {fund}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Suggestions */}
            {messages.length === 1 && suggestions.length > 0 && (
                <div className="suggestions-container">
                    {suggestions.map((sug, i) => (
                        <button
                            key={i}
                            className={`suggestion-pill ${i === 0 ? 'active' : ''}`}
                            onClick={() => handleSuggestionClick(sug)}
                        >
                            {i === 0 && <Star size={16} fill="currentColor" />}
                            {i !== 0 && renderIcon(i)}
                            {sug}
                        </button>
                    ))}
                </div>
            )}

            {/* Chat Area */}
            <div className="chat-area" data-testid="chat-area">
                {messages.map((msg) => (
                    <React.Fragment key={msg.id}>
                        <div className={`message-row ${msg.type}`}>
                            {msg.type === "bot" ? (
                                <div className="avatar bot-avatar"><Bot size={20} color="#fff" /></div>
                            ) : null}

                            <div className="message-bubble">
                                {msg.text}
                                {msg.source && (
                                    <div style={{ marginTop: "8px" }}>
                                        <a href={msg.source} target="_blank" rel="noreferrer" className="source-link">
                                            View Source Reference →
                                        </a>
                                    </div>
                                )}
                            </div>

                            {msg.type === "user" ? (
                                <div className="avatar user-avatar"><User size={20} color="#fff" /></div>
                            ) : null}
                        </div>
                        {msg.type === "bot" && msg.verified && (
                            <div className="bot-footer-text">
                                VERIFIED FINANCIAL INTELLIGENCE
                            </div>
                        )}
                    </React.Fragment>
                ))}

                {loading && (
                    <div className="message-row bot" data-testid="loader">
                        <div className="avatar bot-avatar"><Bot size={20} color="#fff" /></div>
                        <div className="message-bubble" style={{ display: 'flex', alignItems: 'center' }}>
                            <div className="typing-dots">
                                <div className="dot"></div>
                                <div className="dot"></div>
                                <div className="dot"></div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={chatEndRef} />
            </div>

            {/* Bottom Input Zone */}
            <div className="input-area">
                <div className="input-wrapper">
                    <input
                        type="text"
                        className="input-field"
                        placeholder="Ask about funds, performance, or strategy..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && sendMessage(input)}
                        disabled={loading}
                    />
                    <button
                        className="send-button"
                        onClick={() => sendMessage(input)}
                        disabled={loading || !input.trim()}
                    >
                        <Send size={20} />
                    </button>
                </div>
            </div>

            <div className="footer-disclaimer">
                SECURELY PROCESSED BY WEALTHWISE AI ENCRYPTION
            </div>
        </div>
    )
}
