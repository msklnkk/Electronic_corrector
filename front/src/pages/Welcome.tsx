// src/pages/Welcome.tsx
import React from "react";
import {
  Container,
  Typography,
  Button,
  Box,
  Stack,
  Paper,
} from "@mui/material";
import { PictureAsPdf, CheckCircleOutline } from "@mui/icons-material";
import { useNavigate } from "react-router-dom";

const Welcome: React.FC = () => {
  const navigate = useNavigate();

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
    <>
      {/* Герой-секция */}
      <Container maxWidth="md" sx={{ textAlign: "center", py: 10 }}>
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
          onClick={() => navigate("/check")}
          sx={{
            px: 4,
            py: 1.5,
            borderRadius: "12px",
            fontWeight: 600,
            fontSize: "1.1rem",
            boxShadow: "0 0 20px rgba(139,92,246,0.4)",
          }}
        >
          Проверить документ
        </Button>
        <Typography variant="body2" sx={{ color: "text.secondary", mt: 2 }}>
          Без регистрации • Первые 3 проверки бесплатно
        </Typography>
      </Container>

      {/* Преимущества */}
      <Box sx={{ py: 8 }}>
        <Container maxWidth="lg">
          <Typography variant="h4" align="center" sx={{ mb: 6, fontWeight: 700 }}>
            Преимущества платформы
          </Typography>
          <Stack direction={{ xs: "column", md: "row" }} spacing={4} justifyContent="center">
            {features.map((f, i) => (
              <Paper
                key={i}
                elevation={3}
                sx={{
                  flex: 1,
                  p: 4,
                  textAlign: "center",
                  borderRadius: "16px",
                  bgcolor: "background.paper",
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
      <Box sx={{ textAlign: "center", py: 3, borderTop: 1, borderColor: "divider" }}>
        <Typography variant="body2" color="text.secondary">
          © 2025 Электронный корректор
        </Typography>
      </Box>
    </>
  );
};

export default Welcome;