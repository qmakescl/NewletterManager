import React, { useEffect, useState } from 'react';
import './ArticleDetail.css';
import { fetchArticleDetail } from '../api/client';
import { IoClose, IoStar, IoLinkOutline, IoTimeOutline, IoLanguageOutline } from 'react-icons/io5';
import { format } from 'date-fns';

const ArticleDetail = ({ articleId, onClose }) => {
    const [article, setArticle] = useState(null);
    const [loading, setLoading] = useState(true);
    const [lang, setLang] = useState('ko'); // 'ko' or 'en'

    useEffect(() => {
        if (!articleId) return;

        const loadDetail = async () => {
            setLoading(true);
            try {
                const data = await fetchArticleDetail(articleId);
                setArticle(data);
            } catch (error) {
                console.error('Failed to load article detail:', error);
            } finally {
                setLoading(false);
            }
        };
        loadDetail();
    }, [articleId]);

    if (!articleId) return null;

    if (loading) {
        return (
            <div className="article-detail-loading">
                <div className="spinner"></div>
                <p>기사 내용을 불러오는 중...</p>
            </div>
        );
    }

    if (!article) return <div className="detail-error">기사를 찾을 수 없습니다.</div>;

    return (
        <div className="article-detail-container animate-fade-in">
            <header className="detail-header">
                <div className="header-meta">
                    <span className={`category-badge ${article.category.toLowerCase()}`}>
                        {article.category}
                    </span>
                    <div className="importance-stars">
                        {Array.from({ length: 5 }).map((_, i) => (
                            <IoStar key={i} size={14} className={i < article.importance ? 'star active' : 'star'} />
                        ))}
                    </div>
                </div>
                <button className="close-panel-button" onClick={onClose}>
                    <IoClose size={24} />
                </button>
            </header>

            <div className="detail-body">
                <h2 className="detail-title">{article.title}</h2>

                <div className="detail-meta-row">
                    <div className="meta-item">
                        <IoTimeOutline size={16} />
                        <span>{format(new Date(article.published_at), 'yyyy년 MM월 dd일')}</span>
                    </div>
                    <button className="lang-toggle-button" onClick={() => setLang(lang === 'ko' ? 'en' : 'ko')}>
                        <IoLanguageOutline size={16} />
                        {lang === 'ko' ? '영문으로 보기' : '한국어로 보기'}
                    </button>
                </div>

                <div className="detail-summary-section">
                    <h3 className="section-title">{lang === 'ko' ? '기사 요약' : 'Summary'}</h3>
                    <p className={`summary-text ${lang}`}>
                        {lang === 'ko' ? article.summary_ko : article.summary_en}
                    </p>
                </div>

                <div className="detail-tags-section">
                    <h3 className="section-title">Tags</h3>
                    <div className="detail-tags">
                        {article.tags.map(tag => (
                            <span key={tag} className="tag-chip">#{tag}</span>
                        ))}
                    </div>
                </div>
            </div>

            <footer className="detail-footer">
                <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="visit-site-button"
                >
                    원문 기사 방문하기
                    <IoLinkOutline size={18} />
                </a>
            </footer>
        </div>
    );
};

export default ArticleDetail;
