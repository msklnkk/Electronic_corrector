// src/components/LoginForm.tsx
import React, { useState } from 'react';
import { TextField, Button, Box, Alert, Link, Typography } from '@mui/material';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

export const LoginForm: React.FC = () => {
  const [firstName, setFirstName] = useState('');
  const [surname, setSurname] = useState('');
  const [patronomic, setPatronomic] = useState('');
  const [email, setEmail] = useState('');
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
        await register({
          first_name: firstName,
          surname_name: surname,
          patronomic_name: patronomic,
          login: email,
          password,
        });
      } else {
        await authLogin(email, password);
      }
      navigate('/check');
    } catch (err: any) {
      setError(err.message || 'Ошибка');
    }
  };

  return (
    <Box maxWidth={500} mx="auto" mt={6} p={3} boxShadow={3} borderRadius={2}>
      <Typography variant="h5" gutterBottom textAlign="center">
        {isRegister ? 'Регистрация' : 'Вход'}
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <form onSubmit={handleSubmit}>
        {isRegister && (
          <>
            <TextField
              fullWidth
              label="Имя"
              value={firstName}
              onChange={e => setFirstName(e.target.value)}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Фамилия"
              value={surname}
              onChange={e => setSurname(e.target.value)}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Отчество"
              value={patronomic}
              onChange={e => setPatronomic(e.target.value)}
              margin="normal"
              required
            />
          </>
        )}

        <TextField
          fullWidth
          label="Email"
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          margin="normal"
          required
        />
        <TextField
          fullWidth
          label="Пароль"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          margin="normal"
          required
        />

        <Button type="submit" fullWidth variant="contained" sx={{ mt: 2, py: 1.5 }}>
          {isRegister ? 'Зарегистрироваться' : 'Войти'}
        </Button>
      </form>

      <Typography variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
        {isRegister ? 'Уже есть аккаунт? ' : 'Нет аккаунта? '}
        <Link component="button" onClick={() => setIsRegister(!isRegister)} variant="body2">
          {isRegister ? 'Войти' : 'Зарегистрироваться'}
        </Link>
      </Typography>
    </Box>
  );
};