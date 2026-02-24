import React, { useEffect, useState } from 'react';
import './NewsletterCalendar.css';
import { fetchNewsletters, triggerDateSync } from '../api/client';
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
    endOfWeek,
    isBefore,
    isWeekend
} from 'date-fns';
import { IoChevronBack, IoChevronForward } from 'react-icons/io5';

const NewsletterCalendar = ({ selectedDates, onDateToggle }) => {
    const [currentMonth, setCurrentMonth] = useState(new Date());
    const [newsletters, setNewsletters] = useState([]);
    const [syncingDates, setSyncingDates] = useState(new Set());

    const loadNewsletters = async () => {
        try {
            const data = await fetchNewsletters();
            setNewsletters(data.newsletters || []);
        } catch (error) {
            console.error('Failed to load newsletters:', error);
        }
    };

    useEffect(() => {
        loadNewsletters();
    }, []);

    const days = eachDayOfInterval({
        start: startOfWeek(startOfMonth(currentMonth)),
        end: endOfWeek(endOfMonth(currentMonth)),
    });

    const handleDateClick = async (dateStr, hasNewsletter) => {
        if (hasNewsletter) {
            const isSelected = selectedDates.includes(dateStr);
            if (isSelected) {
                onDateToggle(selectedDates.filter(d => d !== dateStr));
            } else {
                onDateToggle([...selectedDates, dateStr]);
            }
        } else {
            // 뉴스레터 없는 날 클릭 → 날짜별 동기화 트리거
            if (syncingDates.has(dateStr)) return;

            setSyncingDates(prev => new Set([...prev, dateStr]));
            try {
                await triggerDateSync(dateStr);
                // 동기화 완료 후 뉴스레터 목록 새로고침
                setTimeout(async () => {
                    await loadNewsletters();
                    setSyncingDates(prev => {
                        const next = new Set(prev);
                        next.delete(dateStr);
                        return next;
                    });
                }, 3000);
            } catch {
                setSyncingDates(prev => {
                    const next = new Set(prev);
                    next.delete(dateStr);
                    return next;
                });
            }
        }
    };

    const isNewsletterDay = (date) => {
        const dateStr = format(date, 'yyyy-MM-dd');
        return newsletters.find(n => n.date === dateStr);
    };

    const isMissingWeekday = (day) => {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return (
            isBefore(day, today) &&
            !isWeekend(day) &&
            !isNewsletterDay(day) &&
            day.getMonth() === currentMonth.getMonth()
        );
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
                    const isMissing = isMissingWeekday(day);
                    const isSyncing = syncingDates.has(dateStr);

                    return (
                        <div
                            key={idx}
                            className={`calendar-day ${isActiveMonth ? '' : 'outside'} ${newsletter ? 'has-newsletter' : ''} ${isSelected ? 'selected' : ''} ${isToday(day) ? 'today' : ''} ${isMissing ? 'missing-newsletter' : ''} ${isSyncing ? 'syncing' : ''}`}
                            onClick={() => isActiveMonth && (newsletter || isMissing) && handleDateClick(dateStr, !!newsletter)}
                        >
                            <span className="day-number">{format(day, 'd')}</span>
                            {newsletter && <span className="article-count-dot">{newsletter.article_count}</span>}
                            {isSyncing && <span className="sync-spinner" />}
                        </div>
                    );
                })}
            </div>

            <div className="selected-chips">
                {selectedDates.sort().map(d => (
                    <div key={d} className="date-chip">
                        {format(new Date(d), 'MM/dd')}
                        <button onClick={() => handleDateClick(d, true)}>×</button>
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
