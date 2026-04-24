// src/pages/Profile.tsx
import { useState, useEffect, useRef } from "react";
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
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  TextField,
  Alert,
  Collapse,
  IconButton,
  InputAdornment,
} from "@mui/material";
import { Edit, Telegram as TelegramIcon, Lock, Visibility, VisibilityOff, PhotoCamera } from "@mui/icons-material";
import { useNavigate } from "react-router-dom";

import { api } from "api";
import type { UserProfile } from "types";
import { API_ROUTES, ROUTES } from "config/constants";
import { AuthService } from "services/auth.service";
import { useAverageCheckTime } from "../hooks/useAverageCheckTime";

const Profile = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { averageTimeFormatted, totalChecks, loading: timeLoading } = useAverageCheckTime(user?.user_id);
  const telegramWidgetRef = useRef<HTMLDivElement>(null);
  const [avatarLoading, setAvatarLoading] = useState(false);


  const [pwOpen, setPwOpen] = useState(false);
  const [pwLoading, setPwLoading] = useState(false);
  const [pwError, setPwError] = useState<string | null>(null);
  const [pwSuccess, setPwSuccess] = useState(false);
  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [pwForm, setPwForm] = useState({ old_password: "", new_password: "", confirm: "" });


  type CheckHistoryItem = {
    check_id: number | string;
    document_id: number;
    checked_at?: string | null;
    score?: number | null;
    result?: string | null;
    type?: "custom" | "gost" | "user_template";
    filename?: string;
  };

  type CheckHistoryRow = CheckHistoryItem & {
    filename: string;
  };

  const [historyLoading, setHistoryLoading] = useState(true);
  const [checkHistory, setCheckHistory] = useState<CheckHistoryRow[]>([]);
  const [historyError, setHistoryError] = useState<string | null>(null);


  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setAvatarLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const response = await api.post<UserProfile>(`/users/${user!.user_id}/avatar`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      });
      setUser(response.data);
      localStorage.setItem("user_avatar", response.data.avatar_data ?? "");

    } catch (err: any) {
      alert(err.response?.data?.detail || "Ошибка загрузки аватара");
    } finally {
      setAvatarLoading(false);
      e.target.value = ""; // сбрасываем input, чтобы можно было загрузить тот же файл повторно
    }
  };


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
        navigate(ROUTES.LOGIN);
        return;
      }

      const userId = AuthService.getCurrentUserId();
      if (!userId) {
        localStorage.removeItem("access_token");
        navigate(ROUTES.LOGIN);
        return;
      }

      try {
        const response = await api.get<UserProfile>(`/users/${userId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUser(response.data);
        AuthService.setUserProfile(response.data);
        localStorage.setItem("user_avatar", response.data.avatar_data ?? "");
      } catch (err: any) {
        if (err.response?.status === 401 || err.response?.status === 403) {
          localStorage.removeItem("access_token");
          navigate(ROUTES.LOGIN);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [navigate]);

  // История проверок (последние 5)
  useEffect(() => {
    const fetchHistory = async () => {
      if (!user?.user_id) return;

      setHistoryLoading(true);
      setHistoryError(null);

      try {
        const res = await api.get<CheckHistoryItem[]>(`/checks`);
        const gostChecks: CheckHistoryItem[] = (res.data ?? []).map((c) => ({ ...c, type: "gost" as const }));

        // Кастомные проверки из localStorage
        const customRaw = localStorage.getItem("customCheckHistory");
        const customChecks: CheckHistoryItem[] = customRaw ? JSON.parse(customRaw) : [];

        // Проверки по пользовательскому шаблону из localStorage
        const templateRaw = localStorage.getItem("userTemplateCheckHistory");
        const templateChecks: CheckHistoryItem[] = templateRaw ? JSON.parse(templateRaw) : [];

        const all = [...gostChecks, ...customChecks, ...templateChecks].sort((a, b) => {
          const ta = a.checked_at ? new Date(a.checked_at).getTime() : 0;
          const tb = b.checked_at ? new Date(b.checked_at).getTime() : 0;
          return tb - ta;
        });

        const last = all.slice(0, 5);

        const uniqueDocIds = Array.from(
          new Set(last.filter((c) => c.type !== "custom").map((c) => c.document_id))
        );
        const docs = await Promise.all(
          uniqueDocIds.map((docId) => api.get<any>(`/documents/full-info/${docId}`))
        );

        const docMap = new Map<number, string>();
        for (const d of docs) {
          if (d?.data?.document_id && d?.data?.filename) {
            docMap.set(d.data.document_id, d.data.filename as string);
          }
        }

        const cleanName = (raw: string) => raw.replace(/^\d+_[a-f0-9]+_/, "") || raw;

        const rows: CheckHistoryRow[] = last.map((c) => ({
          ...c,
          filename: (c.type === "custom" || c.type === "user_template")
            ? cleanName((c as any).filename ?? `Документ #${c.document_id}`)
            : cleanName(docMap.get(c.document_id) ?? `Документ #${c.document_id}`),
        }));

        setCheckHistory(rows);
      } catch (err: any) {
        console.error("Ошибка загрузки истории проверок:", err);
        setHistoryError(err?.response?.data?.detail || "Не удалось загрузить историю проверок");
        setCheckHistory([]);
      } finally {
        setHistoryLoading(false);
      }
    };

    fetchHistory();
  }, [user?.user_id]);

  const formatCheckedAt = (checkedAt?: string | null) => {
    if (!checkedAt) return "—";
    const d = new Date(checkedAt);
    if (Number.isNaN(d.getTime())) return "—";
    return d.toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  };

  if (loading) {
    return (
      <Container sx={{ py: 6 }}>
        <Typography>Загрузка профиля...</Typography>
      </Container>
    );
  }

  if (!user) {
    return null;  
  }

  const initials = (() => {
    const f = user.first_name?.[0];
    const s = user.surname_name?.[0];
    if (f && s) return `${f}${s}`.toUpperCase();
    if (f || s) return (f || s)!.toUpperCase();
    return user.email?.[0]?.toUpperCase() ?? "?"; 
  })();

  const fullName =
    [user.surname_name, user.first_name, user.patronomic_name]
      .filter(Boolean)
      .join(" ") || user.email;

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      <Stack direction={{ xs: "column", md: "row" }} spacing={4} alignItems="flex-start">
        {/* ЛЕВАЯ КОЛОНКА — ПРОФИЛЬ */}
        <Box flex={1} width="100%">
          <div ref={telegramWidgetRef} style={{ display: "none" }} />
          <Paper variant="outlined" sx={{ p: 4, borderRadius: "16px" }}>
            <Box textAlign="center" mb={3}>
              <Box sx={{ position: "relative", width: 110, mx: "auto", mb: 2 }}>
                <Avatar
                  src={user.avatar_data ?? undefined}
                  sx={{
                    width: 110,
                    height: 110,
                    bgcolor: "primary.main",
                    fontSize: "3rem",
                    fontWeight: "bold",
                  }}
                >
                  {!user.avatar_data && initials}
                </Avatar>

                <label htmlFor="avatar-upload">
                  <input
                    id="avatar-upload"
                    type="file"
                    accept="image/jpeg,image/png,image/webp,image/gif"
                    style={{ display: "none" }}
                    onChange={handleAvatarChange}
                  />
                  <IconButton
                    component="span"
                    size="small"
                    disabled={avatarLoading}
                    sx={{
                      position: "absolute",
                      bottom: 0,
                      right: 0,
                      bgcolor: "background.paper",
                      border: "2px solid",
                      borderColor: "primary.main",
                      "&:hover": { bgcolor: "primary.50" },
                    }}
                  >
                    {avatarLoading
                      ? <CircularProgress size={16} />
                      : <PhotoCamera fontSize="small" color="primary" />
                    }
                  </IconButton>
                </label>
              </Box>

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
              onClick={() => navigate("/profile/edit")}
            >
              Редактировать профиль
            </Button>

            <Button
              fullWidth
              variant="outlined"
              startIcon={<Lock />}
              sx={{ mt: 1.5, py: 1.5, borderRadius: 3 }}
              onClick={() => { setPwOpen((v) => !v); setPwError(null); setPwSuccess(false); setPwForm({ old_password: "", new_password: "", confirm: "" }); }}
            >
              {pwOpen ? "Скрыть" : "Изменить пароль"}
            </Button>

            <Collapse in={pwOpen}>
              <Box sx={{ mt: 2 }}>
                {pwSuccess && (
                  <Alert severity="success" sx={{ mb: 2 }}>Пароль успешно изменён</Alert>
                )}
                {pwError && (
                  <Alert severity="error" sx={{ mb: 2 }}>{pwError}</Alert>
                )}
                <Stack spacing={2}>
                  <TextField
                    label="Текущий пароль"
                    type={showOld ? "text" : "password"}
                    size="small"
                    fullWidth
                    value={pwForm.old_password}
                    onChange={(e) => setPwForm((p) => ({ ...p, old_password: e.target.value }))}
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton size="small" onClick={() => setShowOld((v) => !v)}>
                            {showOld ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                  />
                  <TextField
                    label="Новый пароль"
                    type={showNew ? "text" : "password"}
                    size="small"
                    fullWidth
                    value={pwForm.new_password}
                    onChange={(e) => setPwForm((p) => ({ ...p, new_password: e.target.value }))}
                    helperText="Минимум 6 символов"
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton size="small" onClick={() => setShowNew((v) => !v)}>
                            {showNew ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                  />
                  <TextField
                    label="Повторите новый пароль"
                    type="password"
                    size="small"
                    fullWidth
                    value={pwForm.confirm}
                    onChange={(e) => setPwForm((p) => ({ ...p, confirm: e.target.value }))}
                    error={pwForm.confirm.length > 0 && pwForm.confirm !== pwForm.new_password}
                    helperText={pwForm.confirm.length > 0 && pwForm.confirm !== pwForm.new_password ? "Пароли не совпадают" : ""}
                  />
                  <Button
                    variant="contained"
                    fullWidth
                    disabled={pwLoading || !pwForm.old_password || pwForm.new_password.length < 6 || pwForm.new_password !== pwForm.confirm}
                    onClick={async () => {
                      setPwLoading(true);
                      setPwError(null);
                      setPwSuccess(false);
                      try {
                        await api.post(`/users/${user.user_id}/password`, {
                          old_password: pwForm.old_password,
                          new_password: pwForm.new_password,
                        });
                        setPwSuccess(true);
                        setPwForm({ old_password: "", new_password: "", confirm: "" });
                      } catch (err: any) {
                        setPwError(err?.response?.data?.detail || "Ошибка при смене пароля");
                      } finally {
                        setPwLoading(false);
                      }
                    }}
                  >
                    {pwLoading ? "Сохранение..." : "Сохранить пароль"}
                  </Button>
                </Stack>
              </Box>
            </Collapse>
          </Paper>
        </Box>

        {/* ПРАВАЯ КОЛОНКА */}
        <Box flex={2} width="100%">
          <Stack spacing={4}>
            <Paper variant="outlined" sx={{ p: 4, borderRadius: "16px" }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Статистика проверок
              </Typography>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={3} mt={2}>
                {/* Общее количество проверок */}
                <Box flex={1} textAlign="center" bgcolor="primary.50" p={3} borderRadius={3}>
                  {timeLoading ? (
                    <CircularProgress size={32} />
                  ) : (
                    <>
                      <Typography variant="h4" fontWeight="bold" color="primary.main">
                        {totalChecks}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Проверок
                      </Typography>
                    </>
                  )}
                </Box>

                {/* Среднее соответствие */}
                <Box flex={1} textAlign="center" bgcolor="success.50" p={3} borderRadius={3}>
                  {historyLoading ? (
                    <CircularProgress size={32} />
                  ) : (
                    <>
                      <Typography variant="h4" fontWeight="bold" color="success.main">
                        {(() => {
                          // score в БД — целое 0-100; для старых записей берём из result JSON
                          const scores = checkHistory
                            .map((c) => {
                              if (c.score != null && Number.isFinite(c.score) && c.score > 0)
                                return c.score;
                              try {
                                if (c.result) {
                                  const parsed = JSON.parse(c.result);
                                  const s = Number(parsed?.score);
                                  if (Number.isFinite(s) && s > 0) return s;
                                }
                              } catch { /* ignore */ }
                              return null;
                            })
                            .filter((s): s is number => s !== null);
                          if (scores.length === 0) return "-";
                          const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
                          return `${Math.round(avg)}%`;
                        })()}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Соответствие
                      </Typography>
                    </>
                  )}
                </Box>

                {/* Среднее время проверки */}
                <Box flex={1} textAlign="center" bgcolor="info.50" p={3} borderRadius={3}>
                  {timeLoading ? (
                    <CircularProgress size={32} />
                  ) : (
                    <>
                      <Typography variant="h4" fontWeight="bold" color="info.main">
                        {averageTimeFormatted}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Среднее время
                      </Typography>
                    </>
                  )}
                </Box>
              </Stack>
            </Paper>

            <Paper variant="outlined" sx={{ p: 4, borderRadius: "16px" }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                История проверок
              </Typography>

              {historyLoading ? (
                <Box sx={{ mt: 2, display: "flex", justifyContent: "center" }}>
                  <CircularProgress size={32} />
                </Box>
              ) : historyError ? (
                <Typography color="error.main" sx={{ mt: 1 }}>
                  {historyError}
                </Typography>
              ) : checkHistory.length === 0 ? (
                <Typography color="text.secondary" sx={{ mt: 1 }}>
                  У вас пока нет выполненных проверок
                </Typography>
              ) : (
                <List dense sx={{ mt: 1 }}>
                  {checkHistory.map((item) => (
                    <ListItem
                      key={item.check_id}
                      disableGutters
                      sx={{ py: 1.2, borderBottom: "1px solid", borderColor: "divider" }}
                      alignItems="flex-start"
                    >
                      <ListItemText
                        primary={
                          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                            <span>{item.filename}</span>
                            {item.type === "custom" && (
                              <Chip label="Custom" size="small" variant="outlined" color="secondary" />
                            )}
                            {item.type === "user_template" && (
                              <Chip label="Шаблон" size="small" variant="outlined" color="info" />
                            )}
                          </Box>
                        }
                        secondary={formatCheckedAt(item.checked_at)}
                        primaryTypographyProps={{ fontWeight: 600 }}
                      />
                      <Button
                        size="small"
                        variant="outlined"
                        sx={{ ml: 2, mt: 0.5 }}
                        onClick={() => {
                          if (item.type === "custom") {
                            try {
                              const raw = localStorage.getItem(`customResult_${item.check_id}`);
                              if (raw) {
                                navigate("/custom-check/result", { state: JSON.parse(raw) });
                                return;
                              }
                            } catch { /* ignore */ }
                          } else if (item.type === "user_template") {
                            try {
                              const raw = localStorage.getItem(`userTemplateResult_${item.check_id}`);
                              if (raw) {
                                navigate(ROUTES.USER_TEMPLATE_CHECK_RESULT, { state: JSON.parse(raw) });
                                return;
                              }
                            } catch { /* ignore */ }
                          } else {
                            navigate(API_ROUTES.DOCUMENTS.CHECK_RESULT(String(item.check_id)));
                          }
                        }}
                      >
                        Открыть
                      </Button>
                    </ListItem>
                  ))}
                </List>
              )}
            </Paper>

            <Paper variant="outlined" sx={{ p: 4, borderRadius: "16px" }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Последние документы
              </Typography>
              <Typography color="text.secondary">
                {totalChecks === 0 
                  ? "У вас пока нет проверенных документов"
                  : `Всего проверок: ${totalChecks}`
                }
              </Typography>
            </Paper>

            {/* <Paper variant="outlined" sx={{ p: 4, borderRadius: "16px" }}>
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
            </Paper> */}
          </Stack>
        </Box>
      </Stack>
    </Container>
  );
};

export default Profile;