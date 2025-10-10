// Enterprise Design System for Magacin Worker PWA
// Optimized for Zebra Android Handhelds

export const theme = {
  // Color Palette
  colors: {
    background: '#0E1117',
    cardBackground: '#1B1F24',
    accent: '#00C896',
    primary: '#007ACC',
    neutral: '#2C2C2C',
    text: '#E5E7EB',
    textSecondary: '#9CA3AF',
    success: '#00C896',
    warning: '#F59E0B',
    error: '#EF4444',
    border: '#374151',
  },

  // Typography
  typography: {
    fontFamily: '"Inter", "Roboto", -apple-system, BlinkMacSystemFont, sans-serif',
    sizes: {
      xs: '12px',
      sm: '14px',
      base: '16px',
      lg: '18px',
      xl: '20px',
      '2xl': '24px',
    },
    weights: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },

  // Spacing
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    '2xl': '32px',
  },

  // Border Radius
  borderRadius: {
    sm: '4px',
    md: '6px',
    lg: '8px',
    xl: '12px',
  },

  // Shadows
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
    md: '0 1px 4px 0 rgba(0, 0, 0, 0.3)',
    lg: '0 2px 8px 0 rgba(0, 0, 0, 0.4)',
  },

  // Z-index
  zIndex: {
    header: 1000,
    bottomNav: 1000,
    modal: 2000,
    toast: 3000,
  },

  // Breakpoints for responsive design
  breakpoints: {
    mobile: '320px',
    handheld: '480px',
    tablet: '768px',
  },
};

export type Theme = typeof theme;

