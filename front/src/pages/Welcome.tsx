import React, { useState, useMemo } from "react";
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Container,
  Box,
  Typography,
  Paper,
  Button,
  IconButton,
  Input,
  CircularProgress,
  Alert,
  Stack,
} from "@mui/material";
import {
  LightMode,
  DarkMode,
  PictureAsPdf,
  CheckCircle,
  ErrorOutline,
} from "@mui/icons-material";

const GostInspectorApp: React.FC = () => {
  const [mode, setMode] = useState<"light" | "dark">("dark");
  const [fileName, setFileName] = useState("Перетащи PDF сюда");
  const [messages, setMessages] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: { main: "#1976d2" },
          secondary: { main: "#22d3ee" },
        },
      }),
    [mode]
  );

  const handleThemeToggle = () => {
    setMode((prev) => (prev === "light" ? "dark" : "light"));
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type === "application/pdf") {
      setFileName(file.name);
      setMessages([]);
    } else {
      setMessages(["Поддерживается только PDF"]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      setMessages([]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessages(["Файл проверяется..."]);
    setTimeout(() => {
      setMessages(["Проверка завершена (пример)."]);
      setLoading(false);
    }, 2000);
  };

  const features = [
    {
      icon: <CheckCircle />,
      title: "Шрифт и формат",
      desc: "Times New Roman, 14 pt, полуторный интервал, абзацный отступ.",
    },
    {
      icon: <CheckCircle />,
      title: "Поля",
      desc: "Левое 25 мм, правое 15 мм, верх/низ 20 мм.",
    },
    {
      icon: <CheckCircle />,
      title: "Структура",
      desc: "Содержание, введение, заключение, список источников, приложения.",
    },
    {
      icon: <ErrorOutline />,
      title: "Нумерация и оформление",
      desc: "Номера страниц, таблицы, рисунки, формулы по ГОСТ.",
    },
  ];

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
        {/* Header */}
        <Box
          component="header"
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            p: 2,
            borderBottom: 1,
            borderColor: "divider",
          }}
        >
          <Typography variant="h6">Проверка оформления PDF</Typography>
          <IconButton color="inherit" onClick={handleThemeToggle}>
            {mode === "light" ? <DarkMode /> : <LightMode />}
          </IconButton>
        </Box>

        {/* Main */}
        <Container maxWidth="md" sx={{ py: 4 }}>
          {/* Hero */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography
              variant="subtitle2"
              color="primary"
              sx={{ fontWeight: 600 }}
            >
              ГОСТ-инспектор
            </Typography>
            <Typography variant="h5" sx={{ mt: 1, mb: 1 }}>
              Проверка оформления курсовых по ГОСТ
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Загрузи PDF — получи список замечаний и рекомендации по
              исправлению.
            </Typography>
          </Paper>

          {/* File Uploader */}
          <Paper
            sx={{
              p: 3,
              mb: 3,
              textAlign: "center",
              borderStyle: "dashed",
              borderColor: "divider",
              bgcolor: "background.paper",
            }}
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
          >
            <Box sx={{ mb: 2 }}>
              <PictureAsPdf sx={{ fontSize: 40, color: "primary.main" }} />
            </Box>
            <Typography variant="body1" sx={{ fontWeight: 500 }}>
              {fileName}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Перетащи сюда файл или выбери вручную
            </Typography>

            <form onSubmit={handleSubmit}>
                <Stack direction="row" justifyContent="center" spacing={2} sx={{ mt: 3 }}>
                    <Button variant="outlined" component="label">
                    Выбрать PDF
                    <input
                        type="file"
                        accept="application/pdf"
                        onChange={handleFileChange}
                        style={{ display: "none" }}
                    />
                    </Button>
                    <Button
                    type="submit"
                    variant="contained"
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={18} /> : undefined}
                    >
                    {loading ? "Проверяем…" : "Проверить"}
                    </Button>
                </Stack>
            </form>


            {messages.length > 0 && (
              <Box sx={{ mt: 3 }}>
                {messages.map((msg, i) => (
                  <Alert
                    key={i}
                    severity={msg.includes("завершена") ? "success" : "info"}
                    sx={{ mb: 1 }}
                  >
                    {msg}
                  </Alert>
                ))}
              </Box>
            )}
          </Paper>

          {/* Features */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Что проверяем
            </Typography>
            <Stack spacing={2}>
              {features.map((f) => (
                <Alert
                  key={f.title}
                  icon={f.icon}
                  severity="info"
                  sx={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}
                >
                  <Typography fontWeight="bold">{f.title}</Typography>
                  {f.desc}
                </Alert>
              ))}
            </Stack>
          </Paper>
        </Container>

        {/* Footer */}
        <Box
          component="footer"
          sx={{
            textAlign: "center",
            py: 2,
            borderTop: 1,
            borderColor: "divider",
          }}
        >
          <Typography variant="body2" color="text.secondary">
            Прототип для курсовой · React + Material UI
          </Typography>
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default GostInspectorApp;
