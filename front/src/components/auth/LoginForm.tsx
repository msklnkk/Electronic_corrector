// src/components/auth/LoginForm.tsx
import React, { useState } from 'react';
import {
  TextField,
  Button,
  Box,
  Alert,
  Link,
  Typography,
  InputAdornment,
  IconButton,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

import { useAuth } from 'hooks';                  
import { api } from 'api';                                 
import { AuthService } from 'services';               
import { API_ROUTES } from 'config/constants';   

interface LoginFormProps {
  onSuccess?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const [firstName, setFirstName] = useState('');
  const [surname, setSurname] = useState('');
  const [patronomic, setPatronomic] = useState('');
  const [tgUsername, setTgUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const { login: authLogin } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      if (isRegister) {
        await AuthService.register({
          first_name: firstName,
          surname_name: surname,
          patronomic_name: patronomic || ' ',
          login: email,
          password: password,
          tg_username: tgUsername || ' ',
        });
      } else {
        await authLogin(email, password);
      }

      // Загрузка актуального профиля
      const { data } = await api.get(API_ROUTES.AUTH.ME);           // ← используем константу
      AuthService.setUserProfile(data);

      onSuccess?.();
      navigate('/check');
    } catch (err: any) {
      const detail = err?.response?.data?.detail;

      if (Array.isArray(detail)) {
        const msg = detail
          .map((e) => {
            const loc = Array.isArray(e.loc) ? e.loc.join(' → ') : '';
            return loc ? `${loc}: ${e.msg}` : e.msg;
          })
          .join('\n');

        setError(msg || 'Ошибка авторизации');
        return;
      }

      if (typeof detail === 'string') {
        setError(detail);
        return;
      }

      if (detail && typeof detail === 'object') {
        setError(detail.msg || 'Ошибка авторизации');
        return;
      }

      setError('Ошибка авторизации');
    }
  };

  return (
    <Box maxWidth={420} mx="auto">
      <Typography variant="h6" textAlign="center" gutterBottom fontWeight={700}>
        {isRegister ? 'Создание аккаунта' : 'Вход в аккаунт'}
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2, whiteSpace: 'pre-line' }}>
          {error}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        {isRegister && (
          <>
            <TextField
              fullWidth
              label="Имя"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Фамилия"
              value={surname}
              onChange={(e) => setSurname(e.target.value)}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Отчество (по желанию)"
              value={patronomic}
              onChange={(e) => setPatronomic(e.target.value)}
              margin="normal"
            />
            <TextField
              fullWidth
              label="Telegram username"
              value={tgUsername}
              onChange={(e) => setTgUsername(e.target.value.replace(/[@\s]/g, ''))}
              margin="normal"
              placeholder="ivan_ivanov"
              helperText="Без @ и пробелов"
              InputProps={{
                startAdornment: <InputAdornment position="start">@</InputAdornment>,
              }}
            />
          </>
        )}

        <TextField
          fullWidth
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          margin="normal"
          required
        />

        <TextField
          fullWidth
          label="Пароль"
          type={showPassword ? 'text' : 'password'}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          margin="normal"
          required
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowPassword((p) => !p)}>
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        <Button
          type="submit"
          fullWidth
          variant="contained"
          size="large"
          sx={{ mt: 3, py: 1.8, borderRadius: 3 }}
        >
          {isRegister ? 'Зарегистрироваться' : 'Войти'}
        </Button>
      </form>

      <Typography variant="body2" textAlign="center" sx={{ mt: 3, color: 'text.secondary' }}>
        {isRegister ? 'Уже есть аккаунт? ' : 'Нет аккаунта? '}
        <Link
          component="button"
          onClick={() => {
            setIsRegister(!isRegister);
            setError('');
          }}
          sx={{ fontWeight: 600, color: 'primary.main' }}
        >
          {isRegister ? 'Войти' : 'Зарегистрироваться'}
        </Link>
      </Typography>
    </Box>
  );
};