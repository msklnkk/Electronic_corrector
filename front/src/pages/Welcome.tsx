// src/pages/Welcome.tsx
import React from "react";
import {
  Container,
  Typography,
  Button,
  Box,
  Stack,
  Paper,
  Avatar,
  Rating,
  Divider,
  Link,
} from "@mui/material";
import {
  PictureAsPdf,
  CheckCircleOutline,
  UploadFile,
  Analytics,
  Description,
  School,
  Business,
  SupportAgent,
  Email,
  Phone,
  Telegram,
} from "@mui/icons-material";

import { useNavigate } from "react-router-dom";
import { ROUTES } from "config/constants"; 
import { Footer } from "components";

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

  const steps = [
    {
      number: 1,
      title: "Загрузите документ",
      desc: "Перетащите PDF или DOCX файл в специальную область или выберите через проводник",
      icon: <UploadFile />,
    },
    {
      number: 2,
      title: "ИИ анализирует",
      desc: "Система проверяет документ на соответствие ГОСТ и корпоративным стандартам",
      icon: <Analytics />,
    },
    {
      number: 3,
      title: "Получите отчёт",
      desc: "Скачайте подробный отчёт с указанием ошибок и рекомендациями по исправлению",
      icon: <Description />,
    },
  ];

  const audiences = [
    {
      icon: <School color="primary" />,
      title: "Студенты",
      desc: "Проверка курсовых, дипломных работ и рефератов на соответствие требованиям ВУЗа",
      checks: ["Оформление по ГОСТ", "Проверка библиографии"],
    },
    {
      icon: <SupportAgent color="primary" />,
      title: "Преподаватели",
      desc: "Быстрая проверка студенческих работ и научных публикаций",
      checks: ["Массовая проверка", "Детальные отчёты"],
    },
    {
      icon: <Business color="primary" />,
      title: "Организации",
      desc: "Контроль документооборота и соответствие корпоративным стандартам",
      checks: ["API интеграция", "Корпоративные тарифы"],
    },
  ];

  const reviews = [
    {
      name: "Анна Петрова",
      role: "Студентка МГУ",
      text: "Сэкономила массу времени при оформлении диплома. Все ошибки были найдены и исправлены за несколько минут!",
      rating: 5,
      avatar: "A",
    },
    {
      name: "Дмитрий Иванов",
      role: "Преподаватель МИФИ",
      text: "Отличный инструмент для проверки студенческих работ. Теперь могу быстро оценить качество оформления.",
      rating: 5,
      avatar: "D",
    },
    {
      name: "Михаил Сидоров",
      role: "IT-директор",
      text: "Внедрили в компании для проверки технической документации. Результат превзошёл ожидания!",
      rating: 5,
      avatar: "M",
    },
  ];

  return (
    <>
      {/* ГЕРОЙ-СЕКЦИЯ */}
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
          onClick={() => navigate(ROUTES.CHECK)}  
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
      </Container>

      {/* ПРЕИМУЩЕСТВА */}
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

      {/* КАК ЭТО РАБОТАЕТ */}
      <Box sx={{ py: 10, bgcolor: "background.default" }}>
        <Container maxWidth="lg">
          <Typography variant="h4" align="center" sx={{ mb: 2, fontWeight: 700 }}>
            Как это работает
          </Typography>
          <Typography variant="body1" align="center" sx={{ color: "text.secondary", mb: 8 }}>
            Простой процесс в три шага
          </Typography>
          <Stack
            direction={{ xs: "column", md: "row" }}
            spacing={6}
            justifyContent="center"
            alignItems="stretch"
          >
            {steps.map((step) => (
              <Box key={step.number} sx={{ textAlign: "center", flex: 1 }}>
                <Box
                  sx={{
                    width: 80,
                    height: 80,
                    borderRadius: "50%",
                    bgcolor: "primary.main",
                    color: "white",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    mx: "auto",
                    mb: 3,
                    fontWeight: 700,
                    fontSize: "1.5rem",
                    boxShadow: "0 0 20px rgba(139,92,246,0.4)",
                  }}
                >
                  {step.number}
                </Box>
                <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                  {step.title}
                </Typography>
                <Typography variant="body2" sx={{ color: "text.secondary" }}>
                  {step.desc}
                </Typography>
              </Box>
            ))}
          </Stack>
        </Container>
      </Box>

      {/* ДЛЯ КОГО */}
      <Box sx={{ py: 10 }}>
        <Container maxWidth="lg">
          <Typography variant="h4" align="center" sx={{ mb: 2, fontWeight: 700 }}>
            Для кого создан сервис
          </Typography>
          <Typography variant="body1" align="center" sx={{ color: "text.secondary", mb: 8 }}>
            Решение для разных категорий пользователей
          </Typography>
          <Stack direction={{ xs: "column", md: "row" }} spacing={4}>
            {audiences.map((a, i) => (
              <Paper
                key={i}
                sx={{
                  flex: 1,
                  p: 4,
                  borderRadius: "16px",
                  bgcolor: "background.paper",
                  border: "1px solid rgba(255,255,255,0.1)",
                }}
              >
                <Box sx={{ mb: 2, color: "primary.main", fontSize: 40 }}>
                  {a.icon}
                </Box>
                <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                  {a.title}
                </Typography>
                <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>
                  {a.desc}
                </Typography>
                <Stack spacing={1}>
                  {a.checks.map((check, idx) => (
                    <Typography key={idx} variant="body2" color="primary">
                      {check}
                    </Typography>
                  ))}
                </Stack>
              </Paper>
            ))}
          </Stack>
        </Container>
      </Box>

      {/* ОТЗЫВЫ */}
      <Box sx={{ py: 10, bgcolor: "background.default" }}>
        <Container maxWidth="lg">
          <Typography variant="h4" align="center" sx={{ mb: 2, fontWeight: 700 }}>
            Отзывы пользователей
          </Typography>
          <Typography variant="body1" align="center" sx={{ color: "text.secondary", mb: 8 }}>
            Что говорят о нашем сервисе
          </Typography>
          <Stack direction={{ xs: "column", md: "row" }} spacing={4}>
            {reviews.map((r, i) => (
              <Paper
                key={i}
                sx={{
                  flex: 1,
                  p: 4,
                  borderRadius: "16px",
                  bgcolor: "background.paper",
                  border: "1px solid rgba(255,255,255,0.1)",
                }}
              >
                <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                  <Avatar sx={{ bgcolor: "primary.main" }}>{r.avatar}</Avatar>
                  <Box>
                    <Typography variant="subtitle1" fontWeight={600}>
                      {r.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {r.role}
                    </Typography>
                  </Box>
                </Stack>
                <Typography variant="body2" sx={{ mb: 2, color: "text.secondary" }}>
                  "{r.text}"
                </Typography>
                <Rating value={r.rating} readOnly size="small" />
              </Paper>
            ))}
          </Stack>
        </Container>
      </Box>

      {/* CTA БЛОК */}
      <Box
        sx={{
          py: 10,
          background: "linear-gradient(135deg, #a855f7 0%, #ec4899 100%)",
          color: "white",
          textAlign: "center",
        }}
      >
        <Container maxWidth="md">
          <Typography variant="h4" sx={{ mb: 2, fontWeight: 700 }}>
            Готовы начать?
          </Typography>
          <Typography variant="body1" sx={{ mb: 4, opacity: 0.9 }}>
            Проверьте свой документ прямо сейчас
          </Typography>
          <Button
            variant="contained"
            size="large"
            sx={{
              bgcolor: "white",
              color: "#a855f7",
              px: 5,
              py: 1.5,
              borderRadius: "12px",
              fontWeight: 600,
              "&:hover": { bgcolor: "#f8fafc" },
            }}
            startIcon={<UploadFile />}
            onClick={() => navigate(ROUTES.CHECK)}  
          >
            Загрузить документ
          </Button>
        </Container>
      </Box>
    </>
  );
};

export default Welcome;