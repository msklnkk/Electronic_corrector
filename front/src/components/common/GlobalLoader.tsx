// src/components/common/GlobalLoader.tsx
import { Backdrop, CircularProgress, Box, Typography } from "@mui/material";

interface GlobalLoaderProps {
  open: boolean;
  message?: string;
}

export const GlobalLoader: React.FC<GlobalLoaderProps> = ({ open, message }) => {
  return (
    <Backdrop
      sx={{
        color: "#fff",
        zIndex: (theme) => theme.zIndex.drawer + 1,
        background: "rgba(0, 0, 0, 0.8)",
        backdropFilter: "blur(8px)",
      }}
      open={open}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 3,
        }}
      >
        <CircularProgress
          size={60}
          thickness={4}
          sx={{
            color: "primary.main",
          }}
        />
        {message && (
          <Typography variant="h6" sx={{ fontWeight: 500 }}>
            {message}
          </Typography>
        )}
      </Box>
    </Backdrop>
  );
};