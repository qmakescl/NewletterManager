import React, { useState, useEffect } from 'react';
import './App.css';
import { fetchNewsletters } from './api/client';
import SearchBar from './components/SearchBar';
import CategoryFilter from './components/CategoryFilter';
import NewsletterCalendar from './components/NewsletterCalendar';
import ArticleList from './components/ArticleList';
import SyncStatus from './components/SyncStatus';
import ChatPanel from './components/ChatPanel';
import ArticleDetail from './components/ArticleDetail';
import { IoMoon, IoSun } from 'react-icons/io5';

function App() {
    const [theme, setTheme] = useState('light');
    const [selectedDates, setSelectedDates] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState('전체');
    const [searchQuery, setSearchQuery] = useState('');
    const [activeArticleId, setActiveArticleId] = useState(null);
    const [showChat, setShowChat] = useState(false);

    // 초기 날짜 로드 (가장 최신 수신일 선택)
    useEffect(() => {
        const loadInitialData = async () => {
            try {
                const { newsletters } = await fetchNewsletters();
                if (newsletters && newsletters.length > 0) {
                    // 최신 날짜 1개 자동 선택
                    setSelectedDates([newsletters[0].date]);
                }
            } catch (error) {
                console.error('Failed to load initial newsletters:', error);
            }
        };
        loadInitialData();
    }, []);

    const toggleTheme = () => {
        const newTheme = theme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
        document.documentElement.setAttribute('data-theme', newTheme);
    };

    return (
        <div className={`app-container ${theme}`}>
            <header className="app-header">
                <div className="header-left">
                    <h1 className="logo">TLDR AI Archive</h1>
                </div>

                <div className="header-center">
                    <SearchBar onSearch={setSearchQuery} />
                </div>

                <div className="header-right">
                    <SyncStatus />
                    <button className="theme-toggle" onClick={toggleTheme}>
                        {theme === 'light' ? <IoMoon size={20} /> : <IoSunny size={20} />}
                    </button>
                </div>
            </header>

            <main className="app-content">
                <aside className="app-sidebar">
                    <div className="sidebar-section">
                        <h3 className="sidebar-title">Categories</h3>
                        <CategoryFilter
                            selected={selectedCategory}
                            onSelect={setSelectedCategory}
                        />
                    </div>

                    <div className="sidebar-section calendar-section">
                        <h3 className="sidebar-title">Newsletter History</h3>
                        <NewsletterCalendar
                            selectedDates={selectedDates}
                            onDateToggle={setSelectedDates}
                        />
                    </div>
                </aside>

                <section className="app-main-grid">
                    <ArticleList
                        dates={selectedDates}
                        category={selectedCategory}
                        searchQuery={searchQuery}
                        onArticleClick={(id) => {
                            setActiveArticleId(id);
                            setShowChat(false);
                        }}
                    />
                </section>

                {/* 우측 사이드 패널 (상세 또는 채팅) */}
                <aside className={`app-detail-panel ${activeArticleId || showChat ? 'show' : ''}`}>
                    <div className="panel-tabs">
                        <button
                            className={`tab ${!showChat ? 'active' : ''}`}
                            onClick={() => setShowChat(false)}
                        >
                            Detail
                        </button>
                        <button
                            className={`tab ${showChat ? 'active' : ''}`}
                            onClick={() => setShowChat(true)}
                        >
                            AI Chat
                        </button>
                    </div>

                    <div className="panel-content">
                        {showChat ? (
                            <ChatPanel />
                        ) : (
                            <ArticleDetail
                                articleId={activeArticleId}
                                onClose={() => setActiveArticleId(null)}
                            />
                        )}
                    </div>
                </aside>
            </main>
        </div>
    );
}

export default App;
