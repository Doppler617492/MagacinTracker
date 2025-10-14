import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';
const MilestoneAnimation = ({ value, previousValue, milestone, label, icon = '🎯' }) => {
    const [showCelebration, setShowCelebration] = useState(false);
    const [hasReachedMilestone, setHasReachedMilestone] = useState(false);
    useEffect(() => {
        const justReached = previousValue < milestone && value >= milestone;
        const wasAbove = previousValue >= milestone;
        if (justReached && !wasAbove) {
            setShowCelebration(true);
            setHasReachedMilestone(true);
            // Hide celebration after 3 seconds
            const timer = setTimeout(() => {
                setShowCelebration(false);
            }, 3000);
            return () => clearTimeout(timer);
        }
    }, [value, previousValue, milestone]);
    const isAtMilestone = value >= milestone;
    const progress = Math.min((value / milestone) * 100, 100);
    return (_jsxs("div", { className: "milestone-container", children: [_jsxs("div", { className: "milestone-header", children: [_jsx("span", { className: "milestone-icon", children: icon }), _jsx("span", { className: "milestone-label", children: label }), _jsx("span", { className: "milestone-value", children: value })] }), _jsxs("div", { className: "milestone-progress", children: [_jsxs("div", { className: "progress-track", children: [_jsx(motion.div, { className: "progress-fill", initial: { width: `${Math.min((previousValue / milestone) * 100, 100)}%` }, animate: { width: `${progress}%` }, transition: { duration: 0.8, ease: "easeOut" }, style: {
                                    background: isAtMilestone
                                        ? 'linear-gradient(90deg, #10b981, #34d399)'
                                        : 'linear-gradient(90deg, #3b82f6, #60a5fa)'
                                } }), _jsx("div", { className: "milestone-marker", style: { left: '100%' } })] }), _jsxs("span", { className: "milestone-target", children: ["/", milestone] })] }), _jsx(AnimatePresence, { children: showCelebration && (_jsx(motion.div, { className: "celebration-overlay", initial: { opacity: 0, scale: 0.5 }, animate: { opacity: 1, scale: 1 }, exit: { opacity: 0, scale: 1.2 }, transition: { duration: 0.5 }, children: _jsxs(motion.div, { className: "celebration-content", animate: {
                            scale: [1, 1.2, 1],
                            rotate: [0, 5, -5, 0]
                        }, transition: {
                            duration: 0.6,
                            repeat: 2,
                            repeatType: "reverse"
                        }, children: [_jsx("div", { className: "celebration-icon", children: "\uD83C\uDF89" }), _jsx("div", { className: "celebration-text", children: "Milestone dostignut!" })] }) })) }), isAtMilestone && !showCelebration && (_jsx(motion.div, { className: "milestone-badge", initial: { opacity: 0, y: -10 }, animate: { opacity: 1, y: 0 }, transition: { delay: 0.2 }, children: "\u2713 Dostignuto" }))] }));
};
export default MilestoneAnimation;
