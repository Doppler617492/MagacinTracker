import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';

interface MilestoneAnimationProps {
  value: number;
  previousValue: number;
  milestone: number;
  label: string;
  icon?: string;
}

const MilestoneAnimation = ({ 
  value, 
  previousValue, 
  milestone, 
  label, 
  icon = '🎯' 
}: MilestoneAnimationProps) => {
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

  return (
    <div className="milestone-container">
      <div className="milestone-header">
        <span className="milestone-icon">{icon}</span>
        <span className="milestone-label">{label}</span>
        <span className="milestone-value">{value}</span>
      </div>
      
      <div className="milestone-progress">
        <div className="progress-track">
          <motion.div
            className="progress-fill"
            initial={{ width: `${Math.min((previousValue / milestone) * 100, 100)}%` }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            style={{
              background: isAtMilestone 
                ? 'linear-gradient(90deg, #10b981, #34d399)' 
                : 'linear-gradient(90deg, #3b82f6, #60a5fa)'
            }}
          />
          <div 
            className="milestone-marker"
            style={{ left: '100%' }}
          />
        </div>
        <span className="milestone-target">/{milestone}</span>
      </div>

      <AnimatePresence>
        {showCelebration && (
          <motion.div
            className="celebration-overlay"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.2 }}
            transition={{ duration: 0.5 }}
          >
            <motion.div
              className="celebration-content"
              animate={{
                scale: [1, 1.2, 1],
                rotate: [0, 5, -5, 0]
              }}
              transition={{
                duration: 0.6,
                repeat: 2,
                repeatType: "reverse"
              }}
            >
              <div className="celebration-icon">🎉</div>
              <div className="celebration-text">Milestone dostignut!</div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {isAtMilestone && !showCelebration && (
        <motion.div
          className="milestone-badge"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          ✓ Dostignuto
        </motion.div>
      )}
    </div>
  );
};

export default MilestoneAnimation;
