import React, { useEffect, useState } from 'react';
import './NewsletterCalendar.css';
import { fetchNewsletters } from '../api/client';
import {
    format,
    startOfMonth,
    endOfMonth,
    eachDayOfInterval,
    isSameDay,
    addMonths,
    subMonths,
    isToday,
    startOfWeek,
    endOfWeek
} from 'date-fns';
import { IoChevronBack, IoChevronForward } from 'react-icons/io5';

const NewsletterCalendar = ({ selectedDates, onDateToggle }) => {
    const [currentMonth, setCurrentMonth] = useState(new Date());
    const [newsletters, setNewsletters] = useState([]);

    useEffect(() => {
        const loadNewsletters = async () => {
            try {
                const data = await fetchNewsletters();
                setNewsletters(data.newsletters || []);
            } catch (error) {
                console.error('Failed to load newsletters:', error);
            }
        };
        loadNewsletters();
    }, []);

    const days = eachDayOfInterval({
        start: startOfWeek(startOfMonth(currentMonth)),
        end: endOfWeek(endOfMonth(currentMonth)),
    });

    const handleDateClick = (dateStr) => {
        const isSelected = selectedDates.includes(dateStr);
        if (isSelected) {
            onDateToggle(selectedDates.filter(d => d !== dateStr));
        } else {
            onDateToggle([...selectedDates, dateStr]);
        }
    };

    const isNewsletterDay = (date) => {
        const dateStr = format(date, 'yyyy-MM-dd');
        return newsletters.find(n => n.date === dateStr);
    };

    return (
        <div className="calendar-container">
            <div className="calendar-header">
                <span className="current-month-label">
                    {format(currentMonth, 'yyyy년 M월')}
                </span>
                <div className="calendar-nav">
                    <button onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}>
                        <IoChevronBack size={18} />
                    </button>
                    <button onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}>
                        <IoChevronForward size={18} />
                    </button>
                </div>
            </div>

            <div className="calendar-grid">
                {['일', '월', '화', '수', '목', '금', '토'].map(d => (
                    <div key={d} className="calendar-weekday">{d}</div>
                ))}
                {days.map((day, idx) => {
                    const dateStr = format(day, 'yyyy-MM-dd');
                    const newsletter = isNewsletterDay(day);
                    const isSelected = selectedDates.includes(dateStr);
                    const isActiveMonth = day.getMonth() === currentMonth.getMonth();

                    return (
                        <div
                            key={idx}
                            className={`calendar-day ${isActiveMonth ? '' : 'outside'} ${newsletter ? 'has-newsletter' : ''} ${isSelected ? 'selected' : ''} ${isToday(day) ? 'today' : ''}`}
                            onClick={() => newsletter && handleDateClick(dateStr)}
                        >
                            <span className="day-number">{format(day, 'd')}</span>
                            {newsletter && <span className="article-count-dot">{newsletter.article_count}</span>}
                        </div>
                    );
                })}
            </div>

            <div className="selected-chips">
                {selectedDates.sort().map(d => (
                    <div key={d} className="date-chip">
                        {format(new Date(d), 'MM/dd')}
                        <button onClick={() => handleDateClick(d)}>×</button>
                    </div>
                ))}
                {selectedDates.length > 0 && (
                    <button className="reset-button" onClick={() => onDateToggle([])}>초기화</button>
                )}
            </div>
        </div>
    );
};

export default NewsletterCalendar;
