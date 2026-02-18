import React, { useState, useRef, useEffect } from 'react';
import './ChatPanel.css';
import { sendChatMessage } from '../api/client';
import { IoSend, IoPersonCircle, IoLogoAmplify } from 'react-icons/io5';

const ChatPanel = () => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: '안녕하세요! 뉴스레터에 대해 궁금한 점을 질문해 주세요.' }
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isTyping]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || isTyping) return;

        const userMessage = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

        setIsTyping(true);
        try {
            const response = await sendChatMessage(userMessage);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: response.answer,
                sources: response.sources
            }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: '죄송합니다. 답변을 생성하는 중 오류가 발생했습니다.'
            }]);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <div className="chat-panel">
            <div className="chat-messages" ref={scrollRef}>
                {messages.map((msg, idx) => (
                    <div key={idx} className={`chat-message ${msg.role}`}>
                        <div className="message-header">
                            {msg.role === 'assistant' ? <IoLogoAmplify className="ai-icon" /> : <IoPersonCircle className="user-icon" />}
                            <span className="sender-name">{msg.role === 'assistant' ? 'AI Assistant' : 'You'}</span>
                        </div>
                        <div className="message-content">
                            {msg.content}
                        </div>
                        {msg.sources && msg.sources.length > 0 && (
                            <div className="message-sources">
                                <span className="source-label">Sources:</span>
                                <div className="source-list">
                                    {msg.sources.map(s => (
                                        <span key={s} className="source-link">📰 Article #{s.substring(0, 4)}</span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ))}
                {isTyping && (
                    <div className="chat-message assistant typing">
                        <div className="message-header">
                            <IoLogoAmplify className="ai-icon" />
                            <span className="sender-name">AI Assistant</span>
                        </div>
                        <div className="typing-indicator">
                            <span></span><span></span><span></span>
                        </div>
                    </div>
                )}
            </div>

            <form className="chat-input-area" onSubmit={handleSend}>
                <input
                    type="text"
                    placeholder="AI에게 질문하기..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                />
                <button type="submit" disabled={!input.trim() || isTyping}>
                    <IoSend size={18} />
                </button>
            </form>
        </div>
    );
};

export default ChatPanel;
