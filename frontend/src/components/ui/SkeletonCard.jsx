import React from 'react';
import './SkeletonCard.css';

const SkeletonCard = () => {
    return (
        <div className="skeleton-card">
            <div className="skeleton-badge skeleton animate-pulse"></div>
            <div className="skeleton-title skeleton animate-pulse"></div>
            <div className="skeleton-text skeleton animate-pulse"></div>
            <div className="skeleton-text skeleton animate-pulse" style={{ width: '80%' }}></div>
            <div className="skeleton-footer">
                <div className="skeleton-tags">
                    <div className="skeleton-tag skeleton animate-pulse"></div>
                    <div className="skeleton-tag skeleton animate-pulse"></div>
                </div>
                <div className="skeleton-link skeleton animate-pulse"></div>
            </div>
        </div>
    );
};

export default SkeletonCard;
