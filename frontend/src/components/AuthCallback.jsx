import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const AuthCallback = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { updateUser } = useAuth();
    const [error, setError] = useState(null);

    useEffect(() => {
        const handleCallback = async () => {
            const code = searchParams.get('code');
            if (!code) {
                setError('인증 코드가 없습니다.');
                return;
            }

            try {
                const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
                const response = await fetch(
                    `${BASE_URL}/api/auth/callback?code=${encodeURIComponent(code)}`,
                    { credentials: 'include' }
                );

                if (!response.ok) {
                    throw new Error('인증에 실패했습니다.');
                }

                const data = await response.json();
                updateUser(data.user);
                navigate('/', { replace: true });
            } catch (err) {
                console.error('Auth callback failed:', err);
                setError(err.message);
            }
        };

        handleCallback();
    }, [searchParams, navigate, updateUser]);

    if (error) {
        return (
            <div style={{ textAlign: 'center', marginTop: '100px' }}>
                <h2>인증 오류</h2>
                <p>{error}</p>
                <a href="/login">로그인 페이지로 돌아가기</a>
            </div>
        );
    }

    return (
        <div style={{ textAlign: 'center', marginTop: '100px' }}>
            <p>인증 처리 중...</p>
        </div>
    );
};

export default AuthCallback;
