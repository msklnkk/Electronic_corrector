// src/components/Header.tsx
import React from "react";
import {
  AppBar,
  Toolbar,
  Button,
  IconButton,
  Stack,
  Box,
} from "@mui/material";
import { LightMode, DarkMode } from "@mui/icons-material";
import { useNavigate, useLocation } from "react-router-dom";

interface HeaderProps {
  mode: "light" | "dark";
  onThemeToggle: () => void;
}

const Header: React.FC<HeaderProps> = ({ mode, onThemeToggle }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <AppBar
      position="static"
      elevation={0}
      color="transparent"
      sx={{
        borderBottom: 1,
        borderColor: mode === "dark" ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)",
        backdropFilter: "blur(12px)",
        zIndex: 10,
      }}
    >
      <Toolbar
        sx={{
          position: "relative",
          minHeight: 64, // ← ВЕРНУЛИ СТАРУЮ ВЫСОТУ
          px: { xs: 1.5, md: 2 }, // ← УМЕНЬШИЛИ ОТСТУПЫ СБОКУ
          py: 0,
        }}
      >
        {/* ЛОГОТИП — БОЛЬШЕ, НО ВПИСЫВАЕТСЯ */}
        <Box
          component="img"
          src="/logo.png"
          alt="Электронный корректор"
          onClick={() => navigate("/")}
          sx={{
            height: { xs: 44, sm: 50, md: 56 }, // ← БОЛЬШЕ, ЧЕМ БЫЛО
            width: "auto",
            maxWidth: { xs: 140, md: 180 },
            cursor: "pointer",
            userSelect: "none",
            mr: { xs: 1, md: 2 }, // ← ОТСТУП СПРАВА ОТ ЛОГОТИПА
            transition: "transform 0.2s ease",
            "&:hover": {
              transform: "scale(1.05)",
            },
          }}
        />

        {/* НАВИГАЦИЯ — ЦЕНТР ЭКРАНА */}
        <Box
          sx={{
            position: "absolute",
            left: "50%",
            top: "50%",
            transform: "translate(-50%, -50%)",
            display: "flex",
            gap: { xs: 2, md: 3 },
            zIndex: 1,
          }}
        >
          <Button
            color="inherit"
            onClick={() => navigate("/")}
            sx={{
              fontWeight: isActive("/") ? 600 : 400,
              fontSize: { xs: "0.9rem", md: "1rem" },
              position: "relative",
              "&::after": {
                content: '""',
                position: "absolute",
                bottom: -8,
                left: 0,
                width: isActive("/") ? "100%" : 0,
                height: 2,
                bgcolor: "primary.main",
                transition: "width 0.3s ease",
              },
            }}
          >
            Главная
          </Button>
          <Button
            color="inherit"
            onClick={() => navigate("/check")}
            sx={{
              fontWeight: isActive("/check") ? 600 : 400,
              fontSize: { xs: "0.9rem", md: "1rem" },
              position: "relative",
              "&::after": {
                content: '""',
                position: "absolute",
                bottom: -8,
                left: 0,
                width: isActive("/check") ? "100%" : 0,
                height: 2,
                bgcolor: "primary.main",
                transition: "width 0.3s ease",
              },
            }}
          >
            Проверить документ
          </Button>
        </Box>

        {/* КНОПКИ СПРАВА */}
        <Stack
          direction="row"
          spacing={{ xs: 0.5, md: 1 }}
          alignItems="center"
          sx={{ ml: "auto" }}
        >
          <IconButton color="inherit" onClick={onThemeToggle}>
            {mode === "dark" ? <LightMode /> : <DarkMode />}
          </IconButton>
          <Button
            variant="contained"
            color="primary"
            sx={{
              borderRadius: "12px",
              textTransform: "none",
              fontWeight: 600,
              px: { xs: 2, md: 3 },
              fontSize: { xs: "0.85rem", md: "1rem" },
            }}
          >
            Войти
          </Button>
        </Stack>
      </Toolbar>
    </AppBar>
  );
};

export default Header;