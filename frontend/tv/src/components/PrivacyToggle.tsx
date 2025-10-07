import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface PrivacyToggleProps {
  onPrivacyChange: (isPrivate: boolean) => void;
}

const PrivacyToggle = ({ onPrivacyChange }: PrivacyToggleProps) => {
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

  return (
    <motion.div
      className="privacy-toggle"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <button
        onClick={togglePrivacy}
        className={`privacy-button ${isPrivate ? 'private' : 'public'}`}
        title={isPrivate ? 'Prikaži imena' : 'Sakrij imena'}
      >
        <AnimatePresence mode="wait">
          {isPrivate ? (
            <motion.span
              key="private"
              initial={{ opacity: 0, rotate: -90 }}
              animate={{ opacity: 1, rotate: 0 }}
              exit={{ opacity: 0, rotate: 90 }}
              transition={{ duration: 0.2 }}
            >
              🔒
            </motion.span>
          ) : (
            <motion.span
              key="public"
              initial={{ opacity: 0, rotate: -90 }}
              animate={{ opacity: 1, rotate: 0 }}
              exit={{ opacity: 0, rotate: 90 }}
              transition={{ duration: 0.2 }}
            >
              👁️
            </motion.span>
          )}
        </AnimatePresence>
        <span className="privacy-label">
          {isPrivate ? 'Privatno' : 'Javno'}
        </span>
      </button>
    </motion.div>
  );
};

export default PrivacyToggle;
