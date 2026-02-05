// src/components/LoginForm.tsx
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
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import axios from '../api/axios.config';
import { AuthService } from '../services/auth.service';

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

  const { login: authLogin, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      if (isRegister) {
        await AuthService.register({
          first_name: firstName,
          surname_name: surname,
          patronomic_name: patronomic || " ",     
          login: email,                          
          password: password,
          tg_username: tgUsername || " ",                
        });
      } else {
        await authLogin(email, password);
      }

      // Загрузка актуального профиль
      const { data } = await axios.get("/me");
      AuthService.setUserProfile(data);

      onSuccess?.();
      navigate('/check');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка авторизации');
    }
  };

  return (
    <Box maxWidth={420} mx="auto">
      <Typography variant="h6" textAlign="center" gutterBottom fontWeight={700}>
        {isRegister ? 'Создание аккаунта' : 'Вход в аккаунт'}
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

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