// src/components/common/StyledCard.tsx
import { Box } from "@mui/material";
import type { ReactNode } from "react";

interface StyledCardProps {
  children: ReactNode;
}

export const StyledCard: React.FC<StyledCardProps> = ({ children }) => (
  <Box
    sx={{
      background: (theme) =>
        theme.palette.mode === 'dark'
          ? 'rgba(25, 28, 40, 0.9)'
          : 'rgba(255, 255, 255, 0.95)',
      borderRadius: '18px',
      p: 4,
      backdropFilter: 'blur(12px)',
      border: (theme) =>
        theme.palette.mode === 'dark'
          ? '1px solid rgba(255, 255, 255, 0.05)'
          : '1px solid rgba(0, 0, 0, 0.08)',
      boxShadow: (theme) =>
        theme.palette.mode === 'dark'
          ? '0 0 40px rgba(0, 0, 0, 0.6)'
          : '0 4px 12px rgba(0, 0, 0, 0.08)',
    }}
  >
    {children}
  </Box>
);