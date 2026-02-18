import React, { useState, useCallback } from 'react';
import './SearchBar.css';
import { IoSearchOutline, IoCloseCircleOutline } from 'react-icons/io5';

const SearchBar = ({ onSearch }) => {
    const [query, setQuery] = useState('');

    // Debounce 로직 (간단히 수동 구현하거나 외부 앱에서 처리 권장, 여기서는 기초 구현)
    const handleChange = (e) => {
        const val = e.target.value;
        setQuery(val);

        // Antigravity Option A (Alpha) 에서는 debounce 300ms 권장
        // 여기서는 로직만 App으로 전달
        onSearch(val);
    };

    const handleClear = () => {
        setQuery('');
        onSearch('');
    };

    return (
        <div className="search-bar-container">
            <div className="search-bar">
                <IoSearchOutline className="search-icon" size={20} />
                <input
                    type="text"
                    className="search-input"
                    placeholder="뉴스레터 기사 검색 (자연어 검색)..."
                    value={query}
                    onChange={handleChange}
                />
                {query && (
                    <button className="clear-button" onClick={handleClear}>
                        <IoCloseCircleOutline size={20} />
                    </button>
                )}
            </div>
        </div>
    );
};

export default SearchBar;
