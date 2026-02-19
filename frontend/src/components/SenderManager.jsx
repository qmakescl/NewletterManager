import React, { useState, useEffect } from 'react';
import './SenderManager.css';
import { fetchSenders, addSender, updateSender, deleteSender } from '../api/client';
import { IoAdd, IoTrash, IoPencil, IoCheckmark, IoClose } from 'react-icons/io5';
import Toast from './ui/Toast';

const SenderManager = () => {
    const [senders, setSenders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [toast, setToast] = useState(null);

    // 추가 폼
    const [newName, setNewName] = useState('');
    const [newEmail, setNewEmail] = useState('');
    const [adding, setAdding] = useState(false);

    // 인라인 편집
    const [editId, setEditId] = useState(null);
    const [editName, setEditName] = useState('');
    const [editEmail, setEditEmail] = useState('');

    useEffect(() => {
        loadSenders();
    }, []);

    const loadSenders = async () => {
        try {
            const data = await fetchSenders();
            setSenders(data);
        } catch (error) {
            setToast({ message: '발신자 목록을 불러오지 못했습니다.', type: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    const handleAdd = async () => {
        if (!newName.trim() || !newEmail.trim()) {
            setToast({ message: '이름과 이메일을 모두 입력해주세요.', type: 'error' });
            return;
        }
        if (!isValidEmail(newEmail)) {
            setToast({ message: '올바른 이메일 형식을 입력해주세요.', type: 'error' });
            return;
        }

        setAdding(true);
        try {
            const created = await addSender({ name: newName.trim(), email: newEmail.trim() });
            setSenders(prev => [...prev, created]);
            setNewName('');
            setNewEmail('');
            setToast({ message: '발신자가 추가되었습니다.', type: 'success' });
        } catch (error) {
            setToast({ message: error.message || '추가에 실패했습니다.', type: 'error' });
        } finally {
            setAdding(false);
        }
    };

    const handleToggleActive = async (sender) => {
        try {
            const updated = await updateSender(sender.id, { is_active: sender.is_active ? false : true });
            setSenders(prev => prev.map(s => s.id === sender.id ? { ...s, ...updated } : s));
        } catch (error) {
            setToast({ message: '상태 변경에 실패했습니다.', type: 'error' });
        }
    };

    const handleEditStart = (sender) => {
        setEditId(sender.id);
        setEditName(sender.name);
        setEditEmail(sender.email);
    };

    const handleEditSave = async () => {
        if (!editName.trim() || !editEmail.trim()) {
            setToast({ message: '이름과 이메일을 모두 입력해주세요.', type: 'error' });
            return;
        }
        if (!isValidEmail(editEmail)) {
            setToast({ message: '올바른 이메일 형식을 입력해주세요.', type: 'error' });
            return;
        }

        try {
            const updated = await updateSender(editId, { name: editName.trim(), email: editEmail.trim() });
            setSenders(prev => prev.map(s => s.id === editId ? { ...s, ...updated } : s));
            setEditId(null);
            setToast({ message: '발신자 정보가 수정되었습니다.', type: 'success' });
        } catch (error) {
            setToast({ message: error.message || '수정에 실패했습니다.', type: 'error' });
        }
    };

    const handleEditCancel = () => {
        setEditId(null);
    };

    const handleDelete = async (sender) => {
        if (!window.confirm(`"${sender.name}" (${sender.email})을(를) 삭제하시겠습니까?`)) return;

        try {
            await deleteSender(sender.id);
            setSenders(prev => prev.filter(s => s.id !== sender.id));
            setToast({ message: '발신자가 삭제되었습니다.', type: 'success' });
        } catch (error) {
            setToast({ message: '삭제에 실패했습니다.', type: 'error' });
        }
    };

    const handleKeyDown = (e, action) => {
        if (e.key === 'Enter') action();
    };

    if (loading) {
        return <div className="sender-manager-loading">불러오는 중...</div>;
    }

    return (
        <div className="sender-manager">
            <div className="sender-add-form">
                <input
                    type="text"
                    className="sender-input"
                    placeholder="표시 이름 (예: TLDR AI)"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    onKeyDown={(e) => handleKeyDown(e, handleAdd)}
                />
                <input
                    type="email"
                    className="sender-input sender-input-email"
                    placeholder="이메일 주소"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    onKeyDown={(e) => handleKeyDown(e, handleAdd)}
                />
                <button
                    className="sender-add-btn"
                    onClick={handleAdd}
                    disabled={adding}
                    title="발신자 추가"
                >
                    <IoAdd size={18} />
                </button>
            </div>

            {senders.length === 0 ? (
                <div className="sender-empty">등록된 발신자가 없습니다.</div>
            ) : (
                <div className="sender-list">
                    {senders.map(sender => (
                        <div key={sender.id} className={`sender-row ${sender.is_active ? '' : 'inactive'}`}>
                            {editId === sender.id ? (
                                <>
                                    <div className="sender-edit-fields">
                                        <input
                                            type="text"
                                            className="sender-input sender-input-sm"
                                            value={editName}
                                            onChange={(e) => setEditName(e.target.value)}
                                            onKeyDown={(e) => handleKeyDown(e, handleEditSave)}
                                        />
                                        <input
                                            type="email"
                                            className="sender-input sender-input-sm sender-input-email"
                                            value={editEmail}
                                            onChange={(e) => setEditEmail(e.target.value)}
                                            onKeyDown={(e) => handleKeyDown(e, handleEditSave)}
                                        />
                                    </div>
                                    <div className="sender-actions">
                                        <button className="sender-action-btn save" onClick={handleEditSave} title="저장">
                                            <IoCheckmark size={16} />
                                        </button>
                                        <button className="sender-action-btn cancel" onClick={handleEditCancel} title="취소">
                                            <IoClose size={16} />
                                        </button>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className="sender-info">
                                        <span className="sender-name">{sender.name}</span>
                                        <span className="sender-email">{sender.email}</span>
                                    </div>
                                    <div className="sender-actions">
                                        <label className="sender-toggle" title={sender.is_active ? '활성' : '비활성'}>
                                            <input
                                                type="checkbox"
                                                checked={!!sender.is_active}
                                                onChange={() => handleToggleActive(sender)}
                                            />
                                            <span className="toggle-slider"></span>
                                        </label>
                                        <button className="sender-action-btn edit" onClick={() => handleEditStart(sender)} title="수정">
                                            <IoPencil size={14} />
                                        </button>
                                        <button className="sender-action-btn delete" onClick={() => handleDelete(sender)} title="삭제">
                                            <IoTrash size={14} />
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    ))}
                </div>
            )}

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

export default SenderManager;
