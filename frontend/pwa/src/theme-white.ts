// White Enterprise Theme for Magacin Worker PWA
// Inspired by Manhattan WMS, SAP Fiori, and professional handheld systems

export const whiteTheme = {
  // Color Palette - Enterprise White Theme
  colors: {
    // Backgrounds
    background: '#F5F7FA',           // Light gray background
    cardBackground: '#FFFFFF',        // Pure white cards
    panelBackground: '#FAFBFC',      // Subtle gray panels
    
    // Primary & Actions
    primary: '#0066CC',              // Professional blue (SAP-style)
    primaryHover: '#0052A3',         // Darker blue on hover
    primaryLight: '#E6F2FF',         // Light blue tint
    
    // Accent & Success
    accent: '#00875A',               // Professional green (success)
    accentHover: '#006644',
    accentLight: '#E3FCEF',
    
    // Text
    text: '#172B4D',                 // Dark blue-gray (primary text)
    textSecondary: '#5E6C84',        // Medium gray (secondary text)
    textMuted: '#8993A4',            // Light gray (muted text)
    
    // Status Colors
    success: '#00875A',              // Green
    warning: '#FF991F',              // Orange
    error: '#DE350B',                // Red
    info: '#0052CC',                 // Blue
    
    // Borders & Dividers
    border: '#DFE1E6',               // Light gray border
    borderHover: '#C1C7D0',          // Medium gray border
    divider: '#EBECF0',              // Very light gray
    
    // Shadows
    shadow: 'rgba(9, 30, 66, 0.08)',
    shadowHover: 'rgba(9, 30, 66, 0.12)',
    
    // States
    hover: '#F4F5F7',                // Hover background
    active: '#E6F2FF',               // Active/selected background
    disabled: '#F4F5F7',             // Disabled background
    disabledText: '#A5ADBA',         // Disabled text
    
    // Badges & Pills
    badge: {
      new: '#E6F2FF',
      newText: '#0052CC',
      inProgress: '#FFF4E6',
      inProgressText: '#FF991F',
      partial: '#FFEBE6',
      partialText: '#DE350B',
      done: '#E3FCEF',
      doneText: '#00875A',
    },
  },

  // Typography
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Helvetica Neue", sans-serif',
    sizes: {
      xs: '11px',
      sm: '13px',
      base: '14px',
      md: '16px',
      lg: '18px',
      xl: '20px',
      '2xl': '24px',
      '3xl': '30px',
    },
    weights: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeights: {
      tight: 1.2,
      normal: 1.5,
      relaxed: 1.75,
    },
  },

  // Spacing (8px grid system)
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    '2xl': '32px',
    '3xl': '48px',
  },

  // Border Radius
  borderRadius: {
    sm: '4px',
    md: '6px',
    lg: '8px',
    xl: '12px',
    full: '9999px',
  },

  // Shadows (subtle, professional)
  shadows: {
    sm: '0 1px 2px 0 rgba(9, 30, 66, 0.08)',
    md: '0 2px 4px 0 rgba(9, 30, 66, 0.08), 0 0 1px 0 rgba(9, 30, 66, 0.08)',
    lg: '0 4px 8px 0 rgba(9, 30, 66, 0.1), 0 0 1px 0 rgba(9, 30, 66, 0.06)',
    xl: '0 8px 16px 0 rgba(9, 30, 66, 0.12), 0 0 1px 0 rgba(9, 30, 66, 0.08)',
    card: '0 1px 3px 0 rgba(9, 30, 66, 0.08), 0 0 0 1px rgba(9, 30, 66, 0.04)',
  },

  // Z-index
  zIndex: {
    base: 0,
    dropdown: 100,
    sticky: 200,
    header: 1000,
    modal: 2000,
    toast: 3000,
  },

  // Transitions
  transitions: {
    fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
    normal: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
    slow: '300ms cubic-bezier(0.4, 0, 0.2, 1)',
  },

  // Touch targets (optimized for rugged devices)
  touchTargets: {
    min: '48px',          // Minimum tap target
    comfortable: '56px',  // Comfortable tap target
    large: '64px',        // Large tap target (glove-friendly)
  },

  // Icon sizes
  iconSizes: {
    xs: '14px',
    sm: '16px',
    md: '20px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
  },
};

export type WhiteTheme = typeof whiteTheme;

