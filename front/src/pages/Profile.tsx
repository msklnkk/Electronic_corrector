// src/pages/Profile.tsx
import axios from '../api/axios.config';
import React, { useState, useEffect, useRef } from "react";
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
  tg_username?: string | null;
  telegram_id?: number | null;
  is_tg_subscribed?: boolean;
}

const Profile = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const telegramWidgetRef = useRef<HTMLDivElement>(null);

  // ─────────────────────────────────────────────────────────────────────
  // ВСЁ, ЧТО СВЯЗАНО С ПРОВЕРКОЙ ПОДПИСКИ НА ТЕЛЕГРАМ — ЗАКOMМЕНТИРОВАНО
  // ─────────────────────────────────────────────────────────────────────
  // const [checking, setChecking] = useState(false);
  // const [checkError, setCheckError] = useState("");

  // const handleCheckSubscription = async () => {
  //   setChecking(true);
  //   setCheckError("");

  //   try {
  //     const response = await axios.post("/check-tg-subscription");

  //     const { data } = await axios.get("/me");
  //     setUser(data);

  //     if (response.data.subscribed) {
  //       alert("Подписка подтверждена! Доступ открыт.");
  //     } else {
  //       alert("Вы не подписаны. Подпишитесь и попробуйте снова.");
  //     }
  //   } catch (err: any) {
  //     const msg = err.response?.data?.detail || "Ошибка проверки подписки";
  //     setCheckError(msg);
  //     console.error(msg);
  //   } finally {
  //     setChecking(false);
  //   }
  // };

  // ─────────────────────────────────────────────────────────────────────
  // Виджет авторизации Telegram — тоже отключён
  // ─────────────────────────────────────────────────────────────────────
  // useEffect(() => {
  //   if (!telegramWidgetRef.current || user?.tg_username) return;

  //   (window as any).onTelegramAuth = async (tgUser: any) => {
  //     try {
  //       const authData = {
  //         id: tgUser.id,
  //         first_name: tgUser.first_name || '',
  //         last_name: tgUser.last_name || '',
  //         username: tgUser.username || '',
  //         photo_url: tgUser.photo_url || '',
  //         auth_date: tgUser.auth_date,
  //         hash: tgUser.hash,
  //       };

  //       const response = await axios.post("/telegram-auth", authData, {
  //         headers: {
  //           Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  //         },
  //       });

  //       if (response.data.success) {
  //         alert("Telegram успешно привязан и подписка проверена!");
  //         const { data } = await axios.get("/me");
  //         setUser(data);
  //       }
  //     } catch (err: any) {
  //       console.error("Telegram auth error:", err.response?.data);
  //       if (err.response?.status === 403) {
  //         alert("Ошибка подписи или Telegram уже привязан к другому аккаунту");
  //       } else {
  //         alert("Произошла ошибка при привязке Telegram");
  //       }
  //     }
  //   };

  //   const script = document.createElement("script");
  //   script.src = "https://telegram.org/js/telegram-widget.js?22";
  //   script.async = true;
  //   script.setAttribute("data-telegram-login", "elecrtonic_corrector_bot");
  //   script.setAttribute("data-size", "large");
  //   script.setAttribute("data-onauth", "onTelegramAuth(user)");
  //   script.setAttribute("data-request-access", "write");

  //   telegramWidgetRef.current.appendChild(script);

  //   return () => {
  //     if (telegramWidgetRef.current) {
  //       telegramWidgetRef.current.innerHTML = "";
  //     }
  //     delete (window as any).onTelegramAuth;
  //   };
  // }, [user?.tg_username]);

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

              {/* БЛОК TELEGRAM */}
              <Box>
                <Typography variant="body2" color="text.secondary">Telegram</Typography>

                {user.tg_username ? (
                  <Box sx={{ mt: 1.5 }}>
                    <Stack direction="row" alignItems="center" spacing={1.5}>
                      <TelegramIcon color="primary" />
                      <Typography fontWeight={700} color="primary">
                        @{user.tg_username.replace("@", "")}
                      </Typography>
                      {/* Чип с подпиской закомментирован */}
                      {/* {user.is_tg_subscribed ? (
                        <Chip label="Подписан" color="success" size="small" />
                      ) : (
                        <Chip label="Не подписан" color="error" size="small" />
                      )} */}
                    </Stack>

                    {/* Весь блок с кнопками и предупреждениями — закомментирован */}
                    {/* {!user.is_tg_subscribed && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" color="error.main">
                          Подпишитесь на канал, чтобы снять все ограничения на проверку документов
                        </Typography>
                        <Stack direction="row" spacing={2} sx={{ mt: 1.5 }}>
                          <Button
                            variant="contained"
                            size="small"
                            href="https://t.me/electronic_corrector"
                            target="_blank"
                          >
                            Перейти в канал
                          </Button>
                          <Button
                            variant="outlined"
                            size="small"
                            onClick={handleCheckSubscription}
                            disabled={checking}
                          >
                            {checking ? "Проверка..." : "Проверить подписку"}
                          </Button>
                        </Stack>

                        {checkError && (
                          <Typography variant="caption" color="error" sx={{ mt: 1, display: "block" }}>
                            {checkError}
                          </Typography>
                        )}
                      </Box>
                    )} */}
                  </Box>
                ) : (
                  <Box sx={{ mt: 1.5 }}>
                    <Typography fontWeight={500} color="text.secondary">
                      Не привязан
                    </Typography>

                    {/* Виджет авторизации закомментирован */}
                    {/* <Box sx={{ textAlign: "center", minHeight: 80 }}>
                      <div ref={telegramWidgetRef} />
                    </Box> */}
                  </Box>
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