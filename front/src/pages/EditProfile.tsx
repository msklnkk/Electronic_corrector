import React, { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Container,
  IconButton,
  Paper,
  Stack,
  TextField,
  Typography,
  InputAdornment,
} from "@mui/material";
import { Visibility, VisibilityOff } from "@mui/icons-material";
import { useNavigate } from "react-router-dom";

import { api } from "api";
import type { UserProfile } from "types";
import { API_ROUTES, ROUTES } from "config/constants";

type UserEditFields = {
  first_name: string;
  surname_name: string;
  patronomic_name: string;
  username: string;
  email: string;
  password: string;
};

const EditProfilePage: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [showPassword, setShowPassword] = useState(false);

  const [fields, setFields] = useState<UserEditFields>({
    first_name: "",
    surname_name: "",
    patronomic_name: "",
    username: "",
    email: "",
    password: "",
  });

  const navigate = useNavigate();

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem("access_token");
      if (!token) {
        navigate(ROUTES.LOGIN);
        return;
      }

      try {
        const response = await api.get<UserProfile>("/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUser(response.data);
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

  useEffect(() => {
    if (!user) return;
    setFields((prev) => ({
      ...prev,
      first_name: user.first_name ?? "",
      surname_name: user.surname_name ?? "",
      patronomic_name: user.patronomic_name ?? "",
      username: (user as any).username ?? "",
      email: user.email ?? "",
    }));
  }, [user]);

  const canSubmit = useMemo(() => {
    const hasNames =
      fields.first_name.trim().length > 0 &&
      fields.surname_name.trim().length > 0 &&
      fields.username.trim().length > 0 &&
      fields.email.trim().length > 0;

    const hasPassword = fields.password.trim().length >= 6;

    return hasNames && hasPassword;
  }, [fields]);

  const handleSubmit = async () => {
    if (!user) return;
    setSaving(true);
    setError(null);

    try {
      const payload = {
        first_name: fields.first_name.trim(),
        surname_name: fields.surname_name.trim(),
        patronomic_name: fields.patronomic_name.trim(),
        username: fields.username.trim(),
        email: fields.email.trim(),
        password: fields.password,
        role: user.role ?? "user",
        is_admin: (user as any).is_admin ?? false,
        tg_username: (user as any).tg_username ?? null,
        telegram_id: (user as any).telegram_id ?? null,
        is_tg_subscribed: (user as any).is_tg_subscribed ?? false,
        theme: (user as any).theme ?? "light",
        is_push_enabled: (user as any).is_push_enabled ?? false,
      };

      await api.put(API_ROUTES.USERS.UPDATE(user.user_id), payload);
      navigate(ROUTES.PROFILE);
    } catch (err: any) {
      console.error("Ошибка обновления профиля:", err?.response?.data || err);
      setError(err?.response?.data?.detail || err?.message || "Не удалось обновить профиль");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Container sx={{ py: 6 }}>
        <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Stack spacing={3}>
        <Typography variant="h4" fontWeight={700}>
          Редактирование профиля
        </Typography>

        {error && <Alert severity="error">{error}</Alert>}

        <Paper variant="outlined" sx={{ p: 4, borderRadius: "16px" }}>
          <Stack spacing={2}>
            <TextField
              label="Имя"
              value={fields.first_name}
              onChange={(e) => setFields((p) => ({ ...p, first_name: e.target.value }))}
              required
              fullWidth
            />
            <TextField
              label="Фамилия"
              value={fields.surname_name}
              onChange={(e) => setFields((p) => ({ ...p, surname_name: e.target.value }))}
              required
              fullWidth
            />
            <TextField
              label="Отчество"
              value={fields.patronomic_name}
              onChange={(e) => setFields((p) => ({ ...p, patronomic_name: e.target.value }))}
              fullWidth
            />
            <TextField
              label="Логин"
              value={fields.username}
              onChange={(e) => setFields((p) => ({ ...p, username: e.target.value }))}
              required
              fullWidth
            />
            <TextField
              label="Email"
              type="email"
              value={fields.email}
              onChange={(e) => setFields((p) => ({ ...p, email: e.target.value }))}
              required
              fullWidth
            />
            <TextField
              label="Пароль (нужно для обновления)"
              type={showPassword ? "text" : "password"}
              value={fields.password}
              onChange={(e) => setFields((p) => ({ ...p, password: e.target.value }))}
              required
              fullWidth
              helperText="Минимум 6 символов"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => setShowPassword((v) => !v)}>
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <Box sx={{ display: "flex", gap: 2, mt: 2 }}>
              <Button
                variant="outlined"
                fullWidth
                onClick={() => navigate(ROUTES.PROFILE)}
                disabled={saving}
              >
                Назад
              </Button>
              <Button
                variant="contained"
                fullWidth
                onClick={handleSubmit}
                disabled={!canSubmit || saving}
              >
                {saving ? "Сохранение..." : "Сохранить"}
              </Button>
            </Box>
          </Stack>
        </Paper>
      </Stack>
    </Container>
  );
};

export default EditProfilePage;

