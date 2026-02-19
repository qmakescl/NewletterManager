import { mockArticles, mockCategories, mockNewsletters, mockSenders } from './mockData';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * 기사 목록 조회
 * @param {Object} params { dates, category, page, size }
 */
export const fetchArticles = async ({ dates, category, page = 1, size = 12 } = {}) => {
    if (USE_MOCK) {
        await sleep(500); // 로딩 시뮬레이션
        let filtered = [...mockArticles];

        if (dates) {
            const dateArray = Array.isArray(dates) ? dates : dates.split(',');
            filtered = filtered.filter(a => dateArray.some(d => a.published_at.startsWith(d)));
        }

        if (category && category !== '전체') {
            filtered = filtered.filter(a => a.category === category);
        }

        // 정렬 (최신순)
        filtered.sort((a, b) => new Date(b.published_at) - new Date(a.published_at));

        const start = (page - 1) * size;
        const items = filtered.slice(start, start + size);

        return {
            total: filtered.length,
            items,
            selected_dates: Array.isArray(dates) ? dates : (dates ? dates.split(',') : []),
        };
    }

    const queryParams = new URLSearchParams();
    if (dates) queryParams.append('dates', dates);
    if (category) queryParams.append('category', category);
    queryParams.append('page', page);
    queryParams.append('size', size);

    const response = await fetch(`${BASE_URL}/api/articles?${queryParams.toString()}`);
    if (!response.ok) throw new Error('Failed to fetch articles');
    return response.json();
};

/**
 * 기사 상세 조회
 */
export const fetchArticleDetail = async (id) => {
    if (USE_MOCK) {
        await sleep(300);
        const article = mockArticles.find(a => a.id === id);
        if (!article) throw new Error('Article not found');
        return article;
    }

    const response = await fetch(`${BASE_URL}/api/articles/${id}`);
    if (!response.ok) throw new Error('Failed to fetch article detail');
    return response.json();
};

/**
 * 시맨틱 검색
 */
export const searchArticles = async (q) => {
    if (USE_MOCK) {
        await sleep(800);
        const filtered = mockArticles.filter(a =>
            a.title.toLowerCase().includes(q.toLowerCase()) ||
            a.summary_ko.toLowerCase().includes(q.toLowerCase()) ||
            a.tags.some(t => t.toLowerCase().includes(q.toLowerCase()))
        );
        return { total: filtered.length, items: filtered };
    }

    const response = await fetch(`${BASE_URL}/api/search?q=${encodeURIComponent(q)}`);
    if (!response.ok) throw new Error('Search failed');
    return response.json();
};

/**
 * 카테고리 목록 조회
 */
export const fetchCategories = async () => {
    if (USE_MOCK) {
        await sleep(300);
        return mockCategories;
    }

    const response = await fetch(`${BASE_URL}/api/categories`);
    if (!response.ok) throw new Error('Failed to fetch categories');
    return response.json();
};

/**
 * 뉴스레터 날짜 목록 조회
 */
export const fetchNewsletters = async () => {
    if (USE_MOCK) {
        await sleep(300);
        return { newsletters: mockNewsletters };
    }

    const response = await fetch(`${BASE_URL}/api/newsletters`);
    if (!response.ok) throw new Error('Failed to fetch newsletters');
    return response.json();
};

/**
 * 수동 동기화 트리거
 */
export const triggerSync = async () => {
    if (USE_MOCK) {
        await sleep(2000);
        return { status: 'success', message: 'Sync completed' };
    }

    const response = await fetch(`${BASE_URL}/api/sync`, { method: 'POST' });
    if (!response.ok) throw new Error('Sync failed');
    return response.json();
};

/**
 * RAG 채팅 메시지 전송
 */
export const sendChatMessage = async (message) => {
    if (USE_MOCK) {
        await sleep(1500);
        return {
            answer: `"${message}"에 대한 답변입니다. GPT-5와 Claude 4가 최근 가장 주목받는 모델입니다.`,
            sources: ["1", "2"]
        };
    }

    const response = await fetch(`${BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
    });
    if (!response.ok) throw new Error('Chat failed');
    return response.json();
};

/**
 * 발신자 목록 조회
 */
export const fetchSenders = async () => {
    if (USE_MOCK) {
        await sleep(300);
        return mockSenders;
    }

    const response = await fetch(`${BASE_URL}/api/senders`);
    if (!response.ok) throw new Error('Failed to fetch senders');
    return response.json();
};

/**
 * 발신자 추가
 */
export const addSender = async ({ name, email }) => {
    if (USE_MOCK) {
        await sleep(500);
        return { id: Date.now().toString(), name, email, is_active: 1, created_at: new Date().toISOString() };
    }

    const response = await fetch(`${BASE_URL}/api/senders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email }),
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to add sender');
    }
    return response.json();
};

/**
 * 발신자 수정
 */
export const updateSender = async (id, data) => {
    if (USE_MOCK) {
        await sleep(500);
        return { id, ...data };
    }

    const response = await fetch(`${BASE_URL}/api/senders/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to update sender');
    }
    return response.json();
};

/**
 * 발신자 삭제
 */
export const deleteSender = async (id) => {
    if (USE_MOCK) {
        await sleep(500);
        return { status: 'deleted' };
    }

    const response = await fetch(`${BASE_URL}/api/senders/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Failed to delete sender');
    return response.json();
};
