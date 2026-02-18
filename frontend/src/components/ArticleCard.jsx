import React from 'react';
import './ArticleCard.css';
import { IoStar, IoLinkOutline, IoTimeOutline } from 'react-icons/io5';
import { format } from 'date-fns';

const ArticleCard = ({ article, onClick }) => {
    const {
        id,
        title,
        summary_ko,
        category,
        tags,
        importance,
        published_at,
        url
    } = article;

    const renderStars = () => {
        return Array.from({ length: 5 }).map((_, i) => (
            <IoStar
                key={i}
                size={14}
                className={i < importance ? 'star active' : 'star'}
            />
        ));
    };

    return (
        <div className="article-card animate-fade-in" onClick={() => onClick(id)}>
            <div className="card-header">
                <span className={`category-badge ${category.toLowerCase()}`}>
                    {category}
                </span>
                <div className="importance-stars">
                    {renderStars()}
                </div>
            </div>

            <h3 className="article-title">{title}</h3>

            <p className="article-summary">{summary_ko}</p>

            <div className="article-tags">
                {tags.map(tag => (
                    <span key={tag} className="tag-chip">#{tag}</span>
                ))}
            </div>

            <div className="card-footer">
                <div className="publish-date">
                    <IoTimeOutline size={14} />
                    <span>{format(new Date(published_at), 'yyyy.MM.dd')}</span>
                </div>
                <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="link-button"
                    onClick={(e) => e.stopPropagation()}
                >
                    <IoLinkOutline size={18} />
                </a>
            </div>
        </div>
    );
};

export default ArticleCard;
