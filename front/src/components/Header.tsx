// src/components/Header.tsx
import React, { useState, useEffect } from "react";
import {
  AppBar,
  Toolbar,
  Button,
  IconButton,
  Stack,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  Avatar,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Badge,
} from "@mui/material";
import {
  LightMode,
  DarkMode,
  Telegram,
  Person,
  Logout,
} from "@mui/icons-material";
import { useNavigate, useLocation } from "react-router-dom";
import { useTheme } from "@mui/material/styles";
import { LoginForm } from "./LoginForm";
import { AuthService } from "../services/auth.service";

interface HeaderProps {
  mode: "light" | "dark";
  onThemeToggle: () => void;
}

const Header: React.FC<HeaderProps> = ({ mode, onThemeToggle }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const [open, setOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const isAuthenticated = !!AuthService.getToken();
  const user = AuthService.getCurrentUser();

  useEffect(() => {
    if (location.pathname === "/login") {
      setOpen(false);
    }
  }, [location.pathname]);

  const isActive = (path: string) => location.pathname === path;

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => setAnchorEl(null);

  const handleLogout = () => {
    AuthService.logout();
    handleMenuClose();
    navigate("/");
    window.location.reload();
  };

  const getInitials = () => {
    if (!user) return "?";
    const first = user.first_name?.[0];
    const last = user.surname_name?.[0];
    if (first && last) return `${first}${last}`.toUpperCase();
    if (first || last) return (first || last).toUpperCase();
    return user.email?.[0].toUpperCase() || "?";
  };

  const avatarLetter = getInitials();

  return (
    <>
      <AppBar
        position="static"
        elevation={0}
        color="inherit"
        sx={{
          backgroundColor: "background.paper",
          borderBottom: 1,
          borderColor: "divider",
          backdropFilter: "blur(12px)",
        }}
      >
        <Toolbar sx={{ minHeight: 64, px: { xs: 1.5, md: 2 } }}>
          <Box
            component="img"
            src="/logo.png"
            alt="Логотип"
            onClick={() => navigate("/")}
            sx={{ height: 50, cursor: "pointer", mr: 2 }}
          />

          <Box
            sx={{
              position: "absolute",
              left: "50%",
              top: "50%",
              transform: "translate(-50%, -50%)",
              display: "flex",
              gap: 3,
            }}
          >
            <Button
              color="inherit"
              onClick={() => navigate("/")}
              sx={{ fontWeight: isActive("/") ? 600 : 400 }}
            >
              Главная
            </Button>
            <Button
              color="inherit"
              onClick={() => navigate("/check")}
              sx={{ fontWeight: isActive("/check") ? 600 : 400 }}
            >
              Проверить документ
            </Button>
          </Box>

          <Stack direction="row" spacing={1} alignItems="center" sx={{ ml: "auto" }}>
            <IconButton color="inherit" onClick={onThemeToggle}>
              {mode === "dark" ? <LightMode /> : <DarkMode />}
            </IconButton>

            {isAuthenticated ? (
              <>
                <IconButton onClick={handleMenuOpen}>
                  <Badge
                    overlap="circular"
                    anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
                    badgeContent={
                      <Box
                        sx={{
                          width: 14,
                          height: 14,
                          bgcolor: "success.main",
                          borderRadius: "50%",
                          border: "3px solid",
                          borderColor: "background.paper",
                        }}
                      />
                    }
                  >
                    <Avatar
                      sx={{
                        bgcolor: "primary.main",
                        fontWeight: "bold",
                        width: 40,
                        height: 40,
                      }}
                    >
                      {avatarLetter}
                    </Avatar>
                  </Badge>
                </IconButton>

                <Menu
                  anchorEl={anchorEl}
                  open={Boolean(anchorEl)}
                  onClose={handleMenuClose}
                  PaperProps={{ sx: { width: 200, mt: 1, borderRadius: 3 } }}
                  MenuListProps={{ sx: { py: 1 } }}
                >
                  <MenuItem
                    onClick={() => {
                      handleMenuClose();
                      navigate("/profile");
                    }}
                  >
                    <ListItemIcon>
                      <Person fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>Профиль</ListItemText>
                  </MenuItem>
                  <MenuItem onClick={handleLogout} sx={{ color: "error.main" }}>
                    <ListItemIcon>
                      <Logout fontSize="small" sx={{ color: "error.main" }} />
                    </ListItemIcon>
                    <ListItemText>Выйти</ListItemText>
                  </MenuItem>
                </Menu>
              </>
            ) : (
              <Button variant="contained" color="primary" onClick={() => setOpen(true)}>
                Войти
              </Button>
            )}

            <IconButton
              component="a"
              href="https://t.me/electronic_corrector"
              target="_blank"
            >
              <Telegram />
            </IconButton>
          </Stack>
        </Toolbar>
      </AppBar>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle textAlign="center">Вход / Регистрация</DialogTitle>
        <DialogContent>
          <LoginForm
            onSuccess={() => {
              setOpen(false);
              navigate("/check");
            }}
          />
        </DialogContent>
      </Dialog>
    </>
  );
};

export default Header;
