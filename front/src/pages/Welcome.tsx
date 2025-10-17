import React, { useState, useMemo } from "react";
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Container,
  Box,
  Stack,
  Paper,
} from "@mui/material";
import { LightMode, DarkMode, PictureAsPdf, CheckCircleOutline } from "@mui/icons-material";

const Welcome: React.FC = () => {
  const [mode, setMode] = useState<"light" | "dark">("dark");

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: { main: "#8b5cf6" },
          background: {
            default: mode === "dark" ? "#0f172a" : "#f8fafc",
            paper: mode === "dark" ? "#1e293b" : "#ffffff",
          },
          text: {
            primary: mode === "dark" ? "#f8fafc" : "#1e293b",
            secondary: mode === "dark" ? "#cbd5e1" : "#475569",
          },
        },
        typography: {
          fontFamily: "'Inter', 'Roboto', sans-serif",
          h3: { fontWeight: 700 },
        },
      }),
    [mode]
  );

  const handleThemeToggle = () => {
    setMode((prev) => (prev === "light" ? "dark" : "light"));
  };

  const features = [
    {
      icon: <PictureAsPdf fontSize="large" color="primary" />,
      title: "Работа с PDF",
      desc: "Поддержка PDF и DOCX файлов с сохранением форматирования",
    },
    {
      icon: <CheckCircleOutline fontSize="large" color="primary" />,
      title: "ИИ-проверка ГОСТ",
      desc: "Искусственный интеллект анализирует соответствие стандартам",
    },
    {
      icon: <CheckCircleOutline fontSize="large" color="primary" />,
      title: "Отчёт с рекомендациями",
      desc: "Подробный анализ с конкретными советами по исправлению",
    },
  ];

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: "100vh",
          position: "relative",
          overflow: "hidden",
          background: mode === "dark"
            ? "radial-gradient(circle at 20% 20%, rgba(139,92,246,0.2), transparent 50%), radial-gradient(circle at 80% 30%, rgba(147,197,253,0.15), transparent 50%), radial-gradient(circle at 50% 80%, rgba(59,130,246,0.15), transparent 50%), #0f172a"
            : "radial-gradient(circle at 30% 30%, rgba(168,85,247,0.2), transparent 50%), radial-gradient(circle at 80% 60%, rgba(99,102,241,0.15), transparent 50%), #faf5ff",
        }}
      >
        {/* Эффект бликов */}
        <Box
          sx={{
            position: "absolute",
            inset: 0,
            "&::before, &::after": {
              content: '""',
              position: "absolute",
              borderRadius: "50%",
              filter: "blur(100px)",
              opacity: 0.5,
              animation: "moveGlow 20s infinite alternate ease-in-out",
            },
            "&::before": {
              width: 300,
              height: 300,
              background: "rgba(139,92,246,0.35)",
              top: "10%",
              left: "15%",
            },
            "&::after": {
              width: 400,
              height: 400,
              background: "rgba(99,102,241,0.3)",
              bottom: "10%",
              right: "20%",
            },
            "@keyframes moveGlow": {
              "0%": { transform: "translate(0,0)" },
              "100%": { transform: "translate(30px, -30px)" },
            },
          }}
        />

        {/* Навбар */}
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
              justifyContent: "space-between",
              alignItems: "center",
              position: "relative",
            }}
          >
            {/* Левая часть — логотип */}
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Электронный корректор
            </Typography>

            {/* Центр — навигация */}
            <Stack
              direction="row"
              spacing={3}
              sx={{
                position: "absolute",
                left: "50%",
                transform: "translateX(-50%)",
              }}
            >
              <Button color="inherit">Главная</Button>
              <Button color="inherit">Проверить документ</Button>
              <Button color="inherit">Тарифы</Button>
            </Stack>

            {/* Правая часть — тема + профиль */}
            <Stack direction="row" spacing={1} alignItems="center">
              <IconButton color="inherit" onClick={handleThemeToggle}>
                {mode === "dark" ? <LightMode /> : <DarkMode />}
              </IconButton>
              <Button
                variant="contained"
                color="primary"
                sx={{
                  borderRadius: "12px",
                  textTransform: "none",
                  fontWeight: 600,
                  px: 3,
                }}
              >
                Войти
              </Button>
            </Stack>
          </Toolbar>
        </AppBar>

        {/* Герой-секция */}
        <Container maxWidth="md" sx={{ textAlign: "center", py: 10, position: "relative", zIndex: 2 }}>
          <Typography variant="h3" gutterBottom>
            Загрузите файл и получите отчёт об ошибках оформления
          </Typography>
          <Typography variant="body1" sx={{ color: "text.secondary", mb: 4 }}>
            Современная система проверки документов по ГОСТ и корпоративным стандартам
          </Typography>
          <Button
            variant="contained"
            size="large"
            color="primary"
            sx={{
              px: 4,
              py: 1.5,
              borderRadius: "12px",
              fontWeight: 600,
              fontSize: "1.1rem",
              boxShadow: "0 0 20px rgba(139,92,246,0.4)",
            }}
          >
            Попробовать бесплатно
          </Button>
          <Typography variant="body2" sx={{ color: "text.secondary", mt: 2 }}>
            Без регистрации • Первые 3 проверки бесплатно
          </Typography>
        </Container>

        {/* Преимущества */}
        <Box sx={{ bgcolor: "transparent", py: 8, position: "relative", zIndex: 2 }}>
          <Container maxWidth="lg">
            <Typography
              variant="h4"
              align="center"
              sx={{ mb: 6, fontWeight: 700 }}
            >
              Преимущества платформы
            </Typography>
            <Stack
              direction={{ xs: "column", md: "row" }}
              spacing={4}
              justifyContent="center"
              alignItems="stretch"
            >
              {features.map((f, i) => (
                <Paper
                  key={i}
                  elevation={3}
                  sx={{
                    flex: 1,
                    p: 4,
                    textAlign: "center",
                    borderRadius: "16px",
                    bgcolor: mode === "dark" ? "rgba(30,41,59,0.7)" : "#ffffff",
                    backdropFilter: "blur(10px)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    transition: "transform 0.3s",
                    "&:hover": { transform: "translateY(-6px)" },
                  }}
                >
                  <Box sx={{ mb: 2 }}>{f.icon}</Box>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                    {f.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: "text.secondary" }}>
                    {f.desc}
                  </Typography>
                </Paper>
              ))}
            </Stack>
          </Container>
        </Box>

        {/* Подвал */}
        <Box
          sx={{
            textAlign: "center",
            py: 3,
            borderTop: 1,
            borderColor: "divider",
            position: "relative",
            zIndex: 2,
          }}
        >
          <Typography variant="body2" color="text.secondary">
            © 2025 Электронный корректор
          </Typography>
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default Welcome;
