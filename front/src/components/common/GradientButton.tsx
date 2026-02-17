// src/components/common/GradientButton.tsx
import { Box } from "@mui/material";
import type { ReactNode } from "react";

interface GradientButtonProps {
  children: ReactNode;
  color?: "purple" | "cyan" | "pink";
  onClick?: () => void;
}

export const GradientButton: React.FC<GradientButtonProps> = ({ 
  children, 
  color = "purple",
  onClick 
}) => {
  const gradients = {
    purple: "linear-gradient(90deg, #7B5CFF, #9C27B0)",
    cyan: "linear-gradient(90deg, #00E5FF, #00BCD4)",
    pink: "linear-gradient(135deg, #a855f7, #ec4899)",
  };

  return (
    <Box
      onClick={onClick}
      sx={{
        px: 5,
        py: 1.6,
        borderRadius: "12px",
        fontWeight: 600,
        cursor: "pointer",
        textAlign: "center",
        background: gradients[color],
        color: "#fff",
        transition: "0.3s",
        "&:hover": { 
          transform: "translateY(-2px)", 
          opacity: 0.9,
          boxShadow: "0 8px 20px rgba(139, 92, 246, 0.4)",
        },
      }}
    >
      {children}
    </Box>
  );
};