// src/assets/styles/theme.ts
import { createTheme } from '@mui/material/styles';
import type { ThemeOptions } from '@mui/material/styles';

const getThemeOptions = (mode: 'light' | 'dark'): ThemeOptions => ({
  palette: {
    mode,
    primary: {
      main: mode === 'dark' ? '#8b5cf6' : '#7c3aed',
      light: '#a78bfa',
      dark: '#6d28d9',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#ec4899',
      light: '#f472b6',
      dark: '#db2777',
      contrastText: '#ffffff',
    },
    success: {
      main: '#10b981',
      light: '#34d399',
      dark: '#059669',
    },
    error: {
      main: '#ef4444',
      light: '#f87171',
      dark: '#dc2626',
    },
    warning: {
      main: '#f59e0b',
      light: '#fbbf24',
      dark: '#d97706',
    },
    info: {
      main: '#3b82f6',
      light: '#60a5fa',
      dark: '#2563eb',
    },
    background: {
      default: mode === 'dark' ? '#0E1018' : '#f8fafc',
      paper: mode === 'dark' ? 'rgba(25, 28, 40, 0.9)' : '#ffffff',
    },
    text: {
      primary: mode === 'dark' ? '#ffffff' : '#1e293b',
      secondary: mode === 'dark' ? 'rgba(255, 255, 255, 0.7)' : '#64748b',
    },
    divider: mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
  },
  typography: {
    fontFamily: "'Inter', 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    h1: {
      fontWeight: 700,
      fontSize: '3rem',
      lineHeight: 1.2,
    },
    h2: {
      fontWeight: 700,
      fontSize: '2.5rem',
      lineHeight: 1.3,
    },
    h3: {
      fontWeight: 700,
      fontSize: '2rem',
      lineHeight: 1.3,
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.75rem',
      lineHeight: 1.4,
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.5rem',
      lineHeight: 1.4,
    },
    h6: {
      fontWeight: 600,
      fontSize: '1.25rem',
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
    },
    button: {
      fontWeight: 600,
      textTransform: 'none',
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background: mode === 'dark' 
            ? 'radial-gradient(circle at top left, #1B1F2F, #0E1018 60%)'
            : 'linear-gradient(to bottom, #f8fafc, #e2e8f0)',
          minHeight: '100vh',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          padding: '10px 24px',
          fontSize: '1rem',
          fontWeight: 600,
          textTransform: 'none',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
        contained: {
          boxShadow: mode === 'dark'
            ? '0 4px 20px rgba(139, 92, 246, 0.4)'
            : '0 4px 12px rgba(139, 92, 246, 0.3)',
          '&:hover': {
            boxShadow: mode === 'dark'
              ? '0 6px 24px rgba(139, 92, 246, 0.5)'
              : '0 6px 16px rgba(139, 92, 246, 0.4)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          borderRadius: 18,
          ...(mode === 'dark' && {
            background: 'rgba(25, 28, 40, 0.9)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            boxShadow: '0 0 40px rgba(0, 0, 0, 0.6)',
          }),
        },
        elevation1: {
          boxShadow: mode === 'dark' 
            ? '0 1px 3px rgba(0, 0, 0, 0.4)'
            : '0 1px 3px rgba(0, 0, 0, 0.12)',
        },
        elevation3: {
          boxShadow: mode === 'dark'
            ? '0 0 40px rgba(0, 0, 0, 0.6)'
            : '0 4px 6px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 18,
          ...(mode === 'dark' && {
            background: 'rgba(25, 28, 40, 0.9)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
          }),
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
            ...(mode === 'dark' && {
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
            }),
          },
        },
      },
    },
  },
});

export const createAppTheme = (mode: 'light' | 'dark') => {
  return createTheme(getThemeOptions(mode));
};