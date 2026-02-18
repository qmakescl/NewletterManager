import React, { useEffect, useState } from 'react';
import './CategoryFilter.css';
import { fetchCategories } from '../api/client';

const CategoryFilter = ({ selected, onSelect }) => {
    const [categories, setCategories] = useState([]);

    useEffect(() => {
        const loadCategories = async () => {
            try {
                const data = await fetchCategories();
                setCategories(data);
            } catch (error) {
                console.error('Failed to load categories:', error);
            }
        };
        loadCategories();
    }, []);

    return (
        <ul className="category-list">
            <li
                className={`category-item ${selected === '전체' ? 'active' : ''}`}
                onClick={() => onSelect('전체')}
            >
                <span className="category-dot all"></span>
                <span className="category-name">전체</span>
                <span className="category-count">
                    {categories.reduce((acc, cat) => acc + cat.count, 0)}
                </span>
            </li>

            {categories.map((cat) => (
                <li
                    key={cat.name}
                    className={`category-item ${selected === cat.name ? 'active' : ''}`}
                    onClick={() => onSelect(cat.name)}
                >
                    <span className={`category-dot ${cat.name.toLowerCase()}`}></span>
                    <span className="category-name">{cat.name}</span>
                    <span className="category-count">{cat.count}</span>
                </li>
            ))}
        </ul>
    );
};

export default CategoryFilter;
