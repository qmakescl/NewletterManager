import React from 'react';
import './SettingsPage.css';
import { IoArrowBack, IoMail } from 'react-icons/io5';
import SenderManager from './SenderManager';

const SettingsPage = ({ onBack }) => {
    return (
        <div className="settings-page">
            <div className="settings-header">
                <button className="settings-back-btn" onClick={onBack} title="돌아가기">
                    <IoArrowBack size={20} />
                </button>
                <h2 className="settings-title">Settings</h2>
            </div>

            <div className="settings-content">
                <section className="settings-section">
                    <div className="settings-section-header">
                        <IoMail size={20} />
                        <h3>Newsletter Senders</h3>
                    </div>
                    <p className="settings-section-desc">
                        수집할 뉴스레터 발신자를 관리합니다. 활성 상태인 발신자의 이메일만 Gmail에서 수집됩니다.
                    </p>
                    <SenderManager />
                </section>
            </div>
        </div>
    );
};

export default SettingsPage;
