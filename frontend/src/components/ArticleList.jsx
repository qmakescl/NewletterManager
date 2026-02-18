import React, { useEffect, useState } from 'react';
import './ArticleList.css';
import { fetchArticles } from '../api/client';
import ArticleCard from './ArticleCard';
import SkeletonCard from './ui/SkeletonCard';

const ArticleList = ({ dates, category, searchQuery, onArticleClick }) => {
    const [articles, setArticles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);

    useEffect(() => {
        const loadArticles = async () => {
            setLoading(true);
            setError(null);
            try {
                const dateParam = dates.length > 0 ? dates.join(',') : null;
                const data = await fetchArticles({
                    dates: dateParam,
                    category: category === '전체' ? null : category,
                    page,
                    size: 12
                });

                // 검색 쿼리가 있는 경우 프론트엔드 필터링 (Mock 용)
                let items = data.items;
                if (searchQuery) {
                    const q = searchQuery.toLowerCase();
                    items = items.filter(a =>
                        a.title.toLowerCase().includes(q) ||
                        a.summary_ko.toLowerCase().includes(q) ||
                        a.tags.some(t => t.toLowerCase().includes(q))
                    );
                }

                setArticles(items);
                setTotal(data.total);
            } catch (err) {
                setError('데이터를 불러오는데 실패했습니다.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        loadArticles();
    }, [dates, category, searchQuery, page]);

    if (loading && articles.length === 0) {
        return (
            <div className="article-grid">
                {Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)}
            </div>
        );
    }

    if (error) {
        return (
            <div className="list-error">
                <p>{error}</p>
                <button onClick={() => setPage(1)}>다시 시도</button>
            </div>
        );
    }

    if (articles.length === 0) {
        return (
            <div className="list-empty">
                <p>검색 결과가 없습니다. 다른 필터를 선택해 보세요.</p>
            </div>
        );
    }

    return (
        <div className="article-list-container">
            <div className="list-header">
                <h2 className="result-count">기사 총 {total}개</h2>
            </div>

            <div className="article-grid">
                {articles.map(article => (
                    <ArticleCard
                        key={article.id}
                        article={article}
                        onClick={onArticleClick}
                    />
                ))}
            </div>

            {total > 12 && (
                <div className="pagination">
                    <button
                        disabled={page === 1}
                        onClick={() => setPage(p => p - 1)}
                    >
                        이전
                    </button>
                    <span className="page-indicator">{page}</span>
                    <button
                        disabled={page * 12 >= total}
                        onClick={() => setPage(p => p + 1)}
                    >
                        다음
                    </button>
                </div>
            )}
        </div>
    );
};

export default ArticleList;
