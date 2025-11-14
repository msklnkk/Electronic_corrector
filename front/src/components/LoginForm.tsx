// src/components/LoginForm.tsx
import React, { useState } from 'react';
import { TextField, Button, Box, Alert, Link, Typography } from '@mui/material';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

export const LoginForm: React.FC = () => {
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const { login: authLogin, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      if (isRegister) {
        await register(login, password);
      } else {
        await authLogin(login, password);
      }
      navigate('/check');
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <Box maxWidth={400} mx="auto" mt={8} p={3}>
      <Typography variant="h5" gutterBottom>
        {isRegister ? 'Регистрация' : 'Вход'}
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <form onSubmit={handleSubmit}>
        <TextField
          fullWidth label="Логин" value={login} onChange={e => setLogin(e.target.value)}
          margin="normal" required
        />
        <TextField
          fullWidth label="Пароль" type="password" value={password}
          onChange={e => setPassword(e.target.value)} margin="normal" required
        />
        <Button type="submit" fullWidth variant="contained" sx={{ mt: 2 }}>
          {isRegister ? 'Зарегистрироваться' : 'Войти'}
        </Button>
      </form>
      <Typography variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
        {isRegister ? 'Уже есть аккаунт? ' : 'Нет аккаунта? '}
        <Link component="button" onClick={() => setIsRegister(!isRegister)}>
          {isRegister ? 'Войти' : 'Зарегистрироваться'}
        </Link>
      </Typography>
    </Box>
  );
};