import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
const PrivacyToggle = ({ onPrivacyChange }) => {
    const [isPrivate, setIsPrivate] = useState(() => {
        const saved = localStorage.getItem('tv_privacy_mode');
        return saved ? JSON.parse(saved) : false;
    });
    useEffect(() => {
        localStorage.setItem('tv_privacy_mode', JSON.stringify(isPrivate));
        onPrivacyChange(isPrivate);
    }, [isPrivate, onPrivacyChange]);
    const togglePrivacy = () => {
        setIsPrivate(!isPrivate);
    };
    return (_jsx(motion.div, { className: "privacy-toggle", initial: { opacity: 0, scale: 0.8 }, animate: { opacity: 1, scale: 1 }, transition: { duration: 0.3 }, children: _jsxs("button", { onClick: togglePrivacy, className: `privacy-button ${isPrivate ? 'private' : 'public'}`, title: isPrivate ? 'Prikaži imena' : 'Sakrij imena', children: [_jsx(AnimatePresence, { mode: "wait", children: isPrivate ? (_jsx(motion.span, { initial: { opacity: 0, rotate: -90 }, animate: { opacity: 1, rotate: 0 }, exit: { opacity: 0, rotate: 90 }, transition: { duration: 0.2 }, children: "\uD83D\uDD12" }, "private")) : (_jsx(motion.span, { initial: { opacity: 0, rotate: -90 }, animate: { opacity: 1, rotate: 0 }, exit: { opacity: 0, rotate: 90 }, transition: { duration: 0.2 }, children: "\uD83D\uDC41\uFE0F" }, "public")) }), _jsx("span", { className: "privacy-label", children: isPrivate ? 'Privatno' : 'Javno' })] }) }));
};
export default PrivacyToggle;
