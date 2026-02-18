import React, { useEffect, useState } from 'react';
import './Toast.css';

const Toast = ({ message, type = 'success', onClose }) => {
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        const timer = setTimeout(() => {
            setVisible(false);
            setTimeout(onClose, 300); // 닫기 애니메이션 대기
        }, 3000);
        return () => clearTimeout(timer);
    }, [onClose]);

    return (
        <div className={`toast-item ${type} ${visible ? 'show' : 'hide'}`}>
            <span className="toast-message">{message}</span>
        </div>
    );
};

export default Toast;
