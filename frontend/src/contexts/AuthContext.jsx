import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { fetchCurrentUser } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const userData = await fetchCurrentUser();
                setUser(userData);
            } catch {
                setUser(null);
            } finally {
                setLoading(false);
            }
        };
        checkAuth();
    }, []);

    const login = useCallback(async () => {
        const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
        const response = await fetch(`${BASE_URL}/api/auth/login`, {
            credentials: 'include',
        });
        if (!response.ok) throw new Error('Failed to get login URL');
        const data = await response.json();
        window.location.href = data.auth_url;
    }, []);

    const logout = useCallback(async () => {
        const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
        await fetch(`${BASE_URL}/api/auth/logout`, {
            method: 'POST',
            credentials: 'include',
        });
        setUser(null);
        window.location.href = '/login';
    }, []);

    const updateUser = useCallback((userData) => {
        setUser(userData);
    }, []);

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, updateUser }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
