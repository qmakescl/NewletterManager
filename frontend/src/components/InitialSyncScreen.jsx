import React from 'react';
import './InitialSyncScreen.css';
import { IoMailOutline, IoSparkles, IoCheckmarkCircle, IoAlertCircle } from 'react-icons/io5';

const PHASE_CONFIG = {
    gmail_sync: {
        icon: <IoMailOutline className="phase-icon" />,
        step: 1,
    },
    ai_processing: {
        icon: <IoSparkles className="phase-icon" />,
        step: 2,
    },
    done: {
        icon: <IoCheckmarkCircle className="phase-icon done" />,
        step: 3,
    },
    error: {
        icon: <IoAlertCircle className="phase-icon error" />,
        step: 0,
    },
};

const InitialSyncScreen = ({ phase, message }) => {
    const config = PHASE_CONFIG[phase] || PHASE_CONFIG.gmail_sync;

    return (
        <div className="initial-sync-screen">
            <div className="sync-card">
                <div className="sync-logo">
                    <h1 className="sync-logo-text">My News Archive</h1>
                </div>

                <div className="sync-animation">
                    <div className={`sync-ring ${phase === 'done' ? 'complete' : 'active'}`}>
                        {config.icon}
                    </div>
                </div>

                <p className="sync-message">{message || '새로운 뉴스레터를 확인하고 있습니다...'}</p>

                <div className="sync-steps">
                    <div className={`step ${config.step >= 1 ? 'active' : ''} ${config.step > 1 ? 'done' : ''}`}>
                        <span className="step-dot" />
                        <span className="step-label">Gmail 동기화</span>
                    </div>
                    <div className="step-line" />
                    <div className={`step ${config.step >= 2 ? 'active' : ''} ${config.step > 2 ? 'done' : ''}`}>
                        <span className="step-dot" />
                        <span className="step-label">AI 분석</span>
                    </div>
                    <div className="step-line" />
                    <div className={`step ${config.step >= 3 ? 'active' : ''}`}>
                        <span className="step-dot" />
                        <span className="step-label">완료</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InitialSyncScreen;
