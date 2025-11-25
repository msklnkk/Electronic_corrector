// src/pages/Profile.tsx
import axios from '../api/axios.config';
import React, { useState, useEffect } from "react";
import {
  Container,
  Paper,
  Avatar,
  Typography,
  Box,
  Button,
  Stack,
  Chip,
  Divider,
} from "@mui/material";
import { Edit, Telegram as TelegramIcon } from "@mui/icons-material";
import { useNavigate } from "react-router-dom";

interface User {
  user_id: number;
  email: string;
  username: string;
  first_name?: string;
  surname_name?: string;
  patronomic_name?: string;
  role: string;
  theme: string;
  is_push_enabled: boolean;
  tg_username?: string | null;        // ← может быть null!
  is_tg_subscribed?: boolean;
}

const Profile = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem("access_token");
      if (!token) {
        navigate("/login");
        return;
      }

      try {
        const response = await axios.get<User>("/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUser(response.data);
      } catch (err: any) {
        if (err.response?.status === 401 || err.response?.status === 403) {
          localStorage.removeItem("access_token");
          navigate("/login");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [navigate]);

  if (loading) return <Container sx={{ py: 6 }}><Typography>Загрузка профиля...</Typography></Container>;
  if (!user) return null;

  const initials = (() => {
    const f = user.first_name?.[0];
    const s = user.surname_name?.[0];
    if (f && s) return `${f}${s}`.toUpperCase();
    if (f || s) return (f || s)!.toUpperCase();
    return user.email[0].toUpperCase();
  })();

  const fullName = [user.surname_name, user.first_name, user.patronomic_name]
    .filter(Boolean)
    .join(" ") || user.email;

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      <Stack direction={{ xs: "column", md: "row" }} spacing={4} alignItems="flex-start">
        {/* ЛЕВАЯ КОЛОНКА — ПРОФИЛЬ */}
        <Box flex={1} width="100%">
          <Paper variant="outlined" sx={{ p: 4, borderRadius: "16px" }}>
            <Box textAlign="center" mb={3}>
              <Avatar
                sx={{
                  width: 110,
                  height: 110,
                  mx: "auto",
                  mb: 2,
                  bgcolor: "primary.main",
                  fontSize: "3rem",
                  fontWeight: "bold",
                }}
              >
                {initials}
              </Avatar>

              <Typography variant="h5" fontWeight={700}>
                {fullName}
              </Typography>

              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {user.email}
              </Typography>
            </Box>

            <Divider sx={{ mb: 3 }} />

            {/* ВСЯ ИНФОРМАЦИЯ — ЧИТАЕМАЯ */}
            <Stack spacing={2.5}>
              <Box>
                <Typography variant="body2" color="text.secondary">Логин</Typography>
                <Typography fontWeight={600}>{user.email}</Typography>
              </Box>

              {user.first_name && (
                <Box>
                  <Typography variant="body2" color="text.secondary">Имя</Typography>
                  <Typography fontWeight={600}>{user.first_name}</Typography>
                </Box>
              )}

              {user.surname_name && (
                <Box>
                  <Typography variant="body2" color="text.secondary">Фамилия</Typography>
                  <Typography fontWeight={600}>{user.surname_name}</Typography>
                </Box>
              )}

              {user.patronomic_name && user.patronomic_name.trim() && (
                <Box>
                  <Typography variant="body2" color="text.secondary">Отчество</Typography>
                  <Typography fontWeight={600}>{user.patronomic_name}</Typography>
                </Box>
              )}

              {/* ТЕЛЕГРАМ — ГАРАНТИРОВАННО ВИДЕН */}
              <Box>
                <Typography variant="body2" color="text.secondary">Telegram</Typography>
                {user.tg_username ? (
                  <Typography fontWeight={700} color="primary" sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <TelegramIcon fontSize="small" /> @{user.tg_username}
                  </Typography>
                ) : (
                  <Typography fontWeight={500} color="text.secondary">
                    Не указан
                  </Typography>
                )}
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary">Роль</Typography>
                <Typography fontWeight={600}>
                  {user.role === "admin" ? "Администратор" : "Пользователь"}
                </Typography>
              </Box>
            </Stack>

            <Button
              fullWidth
              variant="contained"
              startIcon={<Edit />}
              sx={{ mt: 4, py: 1.8, borderRadius: 3 }}
            >
              Редактировать профиль
            </Button>
          </Paper>
        </Box>

        {/* ПРАВАЯ КОЛОНКА — БЕЗ ТЕЛЕГРАМА, ТОЛЬКО ПУШ */}
        <Box flex={2} width="100%">
          <Stack spacing={4}>
            <Paper variant="outlined" sx={{ p: 4, borderRadius: "16px" }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Статистика проверок
              </Typography>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={3} mt={2}>
                <Box flex={1} textAlign="center" bgcolor="primary.50" p={3} borderRadius={3}>
                  <Typography variant="h4" fontWeight="bold" color="primary.main">247</Typography>
                  <Typography variant="body2" color="text.secondary">Документов</Typography>
                </Box>
                <Box flex={1} textAlign="center" bgcolor="success.50" p={3} borderRadius={3}>
                  <Typography variant="h4" fontWeight="bold" color="success.main">94.2%</Typography>
                  <Typography variant="body2" color="text.secondary">Соответствие</Typography>
                </Box>
                <Box flex={1} textAlign="center" bgcolor="info.50" p={3} borderRadius={3}>
                  <Typography variant="h4" fontWeight="bold" color="info.main">12 мин</Typography>
                  <Typography variant="body2" color="text.secondary">Среднее время</Typography>
                </Box>
              </Stack>
            </Paper>

            <Paper variant="outlined" sx={{ p: 4, borderRadius: "16px" }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Последние документы
              </Typography>
              <Typography color="text.secondary">
                У вас пока нет проверенных документов
              </Typography>
            </Paper>

            <Paper variant="outlined" sx={{ p: 4, borderRadius: "16px" }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Уведомления в браузере
              </Typography>
              <Box sx={{ mt: 2, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Typography>Push-уведомления</Typography>
                <Chip
                  label={user.is_push_enabled ? "Включены" : "Отключены"}
                  color={user.is_push_enabled ? "success" : "default"}
                />
              </Box>
            </Paper>
          </Stack>
        </Box>
      </Stack>
    </Container>
  );
};

export default Profile;