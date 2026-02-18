import React, { useState } from 'react';
import './SyncStatus.css';
import { triggerSync } from '../api/client';
import { IoSync } from 'react-icons/io5';
import Toast from './ui/Toast';

const SyncStatus = () => {
    const [syncing, setSyncing] = useState(false);
    const [toast, setToast] = useState(null);
    const [lastSync, setLastSync] = useState(new Date().toLocaleString('ko-KR'));

    const handleSync = async () => {
        if (syncing) return;

        setSyncing(true);
        try {
            await triggerSync();
            setLastSync(new Date().toLocaleString('ko-KR'));
            setToast({ message: '동기화가 완료되었습니다!', type: 'success' });
        } catch (error) {
            setToast({ message: '동기화 중 오류가 발생했습니다.', type: 'error' });
        } finally {
            setSyncing(false);
        }
    };

    return (
        <div className="sync-status">
            <span className="last-sync-text">최근 동기화: {lastSync}</span>
            <button
                className={`sync-button ${syncing ? 'syncing' : ''}`}
                onClick={handleSync}
                disabled={syncing}
                title="Gmail 동기화"
            >
                <IoSync size={20} />
            </button>

            {toast && (
                <Toast
                    message={toast.message}
                    type={toast.type}
                    onClose={() => setToast(null)}
                />
            )}
        </div>
    );
};

export default SyncStatus;
