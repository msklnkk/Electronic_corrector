// src/components/Header.tsx
import React, { useState } from "react";
import {
  AppBar, Toolbar, Button, IconButton, Stack, Box,
  Dialog, DialogTitle, DialogContent, Tabs, Tab
} from "@mui/material";
import { LightMode, DarkMode, Telegram } from "@mui/icons-material";
import { useNavigate, useLocation } from "react-router-dom";
import { LoginForm } from "./LoginForm";
import { AuthService } from "../services/auth.service";

interface HeaderProps {
  mode: "light" | "dark";
  onThemeToggle: () => void;
}

const Header: React.FC<HeaderProps> = ({ mode, onThemeToggle }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const isAuthenticated = !!AuthService.getToken();

  const isActive = (path: string) => location.pathname === path;

  const handleLogout = () => {
    AuthService.logout();
    navigate("/");
    window.location.reload();
  };

  return (
    <>
      <AppBar position="static" elevation={0} color="transparent" sx={{
        borderBottom: 1,
        borderColor: mode === "dark" ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)",
        backdropFilter: "blur(12px)",
        zIndex: 10,
      }}>
        <Toolbar sx={{
          position: "relative",
          minHeight: 64,
          px: { xs: 1.5, md: 2 },
          py: 0,
        }}>
          {/* ЛОГОТИП */}
          <Box
            component="img"
            src="/logo.png"
            alt="Электронный корректор"
            onClick={() => navigate("/")}
            sx={{
              height: { xs: 44, sm: 50, md: 56 },
              width: "auto",
              maxWidth: { xs: 140, md: 180 },
              cursor: "pointer",
              userSelect: "none",
              mr: { xs: 1, md: 2 },
              transition: "transform 0.2s ease",
              "&:hover": { transform: "scale(1.05)" },
            }}
          />

          {/* НАВИГАЦИЯ */}
          <Box sx={{
            position: "absolute",
            left: "50%",
            top: "50%",
            transform: "translate(-50%, -50%)",
            display: "flex",
            gap: { xs: 2, md: 3 },
            zIndex: 1,
          }}>
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
          <Stack direction="row" spacing={{ xs: 0.5, md: 1 }} alignItems="center" sx={{ ml: "auto" }}>
            <IconButton color="inherit" onClick={onThemeToggle}>
              {mode === "dark" ? <LightMode /> : <DarkMode />}
            </IconButton>

            {isAuthenticated ? (
              <Button
                variant="contained"
                color="error"
                onClick={handleLogout}
                sx={{
                  borderRadius: "12px",
                  textTransform: "none",
                  fontWeight: 600,
                  px: { xs: 2, md: 3 },
                  fontSize: { xs: "0.85rem", md: "1rem" },
                }}
              >
                Выйти
              </Button>
            ) : (
              <Button
                variant="contained"
                color="primary"
                onClick={() => setOpen(true)}
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
            )}

            <IconButton
              component="a"
              href="https://t.me/elecrtonic_corrector"
              target="_blank"
              rel="noopener"
              sx={{
                bgcolor: "rgba(255,255,255,0.1)",
                "&:hover": { bgcolor: "rgba(255,255,255,0.2)" },
                ml: 1,
              }}
            >
              <Telegram sx={{ color: "#229ED9" }} />
            </IconButton>
          </Stack>
        </Toolbar>
      </AppBar>

      {/* МОДАЛКА АВТОРИЗАЦИИ */}
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Tabs value={0} centered>
            <Tab label="Вход / Регистрация" />
          </Tabs>
        </DialogTitle>
        <DialogContent>
          <LoginForm onSuccess={() => { setOpen(false); navigate("/check"); }} />
        </DialogContent>
      </Dialog>
    </>
  );
};

export default Header;