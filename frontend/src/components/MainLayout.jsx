import React, { useState, useEffect, useRef, useCallback } from 'react';
import { fetchNewsletters, fetchSyncStatus, fetchSenders, triggerSync } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import SearchBar from './SearchBar';
import CategoryFilter from './CategoryFilter';
import NewsletterCalendar from './NewsletterCalendar';
import ArticleList from './ArticleList';
import SyncStatus from './SyncStatus';
import ChatPanel from './ChatPanel';
import ArticleDetail from './ArticleDetail';
import SettingsPage from './SettingsPage';
import InitialSyncScreen from './InitialSyncScreen';
import { IoMoon, IoSunny, IoSettings, IoLogOut, IoPerson } from 'react-icons/io5';

function MainLayout() {
    const { user, logout } = useAuth();
    const [theme, setTheme] = useState('light');
    const [selectedDates, setSelectedDates] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState('전체');
    const [searchQuery, setSearchQuery] = useState('');
    const [activeArticleId, setActiveArticleId] = useState(null);
    const [showChat, setShowChat] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const [showOnboarding, setShowOnboarding] = useState(false);
    const [initialSyncing, setInitialSyncing] = useState(true);
    const [syncPhase, setSyncPhase] = useState('gmail_sync');
    const [syncMessage, setSyncMessage] = useState('새로운 뉴스레터를 확인하고 있습니다...');
    const pollRef = useRef(null);

    const startPolling = useCallback(() => {
        pollRef.current = setInterval(async () => {
            try {
                const status = await fetchSyncStatus();
                setSyncPhase(status.phase);
                if (status.message) setSyncMessage(status.message);

                if (status.phase === 'done' || status.phase === 'error') {
                    clearInterval(pollRef.current);
                    setTimeout(async () => {
                        try {
                            const { newsletters } = await fetchNewsletters();
                            if (newsletters && newsletters.length > 0) {
                                setSelectedDates([newsletters[0].date]);
                            }
                        } catch (e) {
                            console.error('Failed to load newsletters after sync:', e);
                        }
                        setInitialSyncing(false);
                    }, status.phase === 'done' ? 1200 : 2000);
                }
            } catch (e) {
                console.error('Failed to poll sync status:', e);
            }
        }, 2000);
    }, []);

    useEffect(() => {
        const init = async () => {
            try {
                // 발신자 0개 → 온보딩 표시
                const senders = await fetchSenders();
                if (!senders || senders.length === 0) {
                    setInitialSyncing(false);
                    setShowOnboarding(true);
                    return;
                }

                const { newsletters } = await fetchNewsletters();
                if (newsletters && newsletters.length > 0) {
                    setSelectedDates([newsletters[0].date]);
                    setInitialSyncing(false);
                    // 기존 데이터 있으면 백그라운드 2일 동기화
                    try {
                        await triggerSync();
                    } catch {
                        // 이미 진행 중이면 무시
                    }
                    return;
                }

                // DB 비어있음 → 동기화 시작
                await triggerSync();
                startPolling();
            } catch (error) {
                if (error.message?.includes('409') || error.message?.includes('Sync failed')) {
                    startPolling();
                } else {
                    console.error('Initial sync failed:', error);
                    setSyncPhase('error');
                    setSyncMessage('동기화를 시작할 수 없습니다. 페이지를 새로고침해주세요.');
                }
            }
        };
        init();

        return () => {
            if (pollRef.current) clearInterval(pollRef.current);
        };
    }, [startPolling]);

    const toggleTheme = () => {
        const newTheme = theme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
        document.documentElement.setAttribute('data-theme', newTheme);
    };

    if (initialSyncing) {
        return <InitialSyncScreen phase={syncPhase} message={syncMessage} />;
    }

    return (
        <div className={`app-container ${theme}`}>
            {showOnboarding && (
                <div className="onboarding-overlay">
                    <div className="onboarding-card">
                        <h2>My News Archive에 오신 것을 환영합니다!</h2>
                        <p>뉴스레터를 수집하려면 먼저 발신자를 등록해주세요.</p>
                        <button
                            className="onboarding-btn"
                            onClick={() => { setShowOnboarding(false); setShowSettings(true); }}
                        >
                            발신자 등록하러 가기
                        </button>
                    </div>
                </div>
            )}
            <header className="app-header">
                <div className="header-left">
                    <h1 className="logo">My News Archive</h1>
                </div>

                <div className="header-center">
                    <SearchBar onSearch={setSearchQuery} />
                </div>

                <div className="header-right">
                    <SyncStatus />
                    {user && (
                        <div className="user-profile" title={user.email}>
                            {user.picture_url ? (
                                <img src={user.picture_url} alt="" className="user-avatar" referrerPolicy="no-referrer" />
                            ) : (
                                <IoPerson size={18} />
                            )}
                        </div>
                    )}
                    <button className="theme-toggle" onClick={() => setShowSettings(true)} title="Settings">
                        <IoSettings size={20} />
                    </button>
                    <button className="theme-toggle" onClick={toggleTheme}>
                        {theme === 'light' ? <IoMoon size={20} /> : <IoSunny size={20} />}
                    </button>
                    <button className="theme-toggle" onClick={logout} title="로그아웃">
                        <IoLogOut size={20} />
                    </button>
                </div>
            </header>

            {showSettings ? (
                <main className="app-content">
                    <SettingsPage onBack={() => setShowSettings(false)} />
                </main>
            ) : (
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
            )}
        </div>
    );
}

export default MainLayout;
