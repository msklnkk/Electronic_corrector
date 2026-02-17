// src/pages/Login.tsx
import React from 'react';
import { Container, Paper, Typography } from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';

import { LoginForm } from 'components/auth';            
import { ROUTES } from 'config/constants';              

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: string })?.from || ROUTES.CHECK;

  return (
    <Container maxWidth="sm" sx={{ mt: 8, minHeight: '70vh', display: 'flex', alignItems: 'center' }}>
      <Paper elevation={6} sx={{ p: 5, borderRadius: 4, width: '100%' }}>
        <Typography variant="h4" component="h1" gutterBottom textAlign="center" fontWeight={700}>
          Вход в аккаунт
        </Typography>
        <Typography variant="body1" color="text.secondary" textAlign="center" mb={4}>
          Войдите, чтобы продолжить
        </Typography>

        <LoginForm
          onSuccess={() => {
            navigate(from, { replace: true });  
          }}
        />
      </Paper>
    </Container>
  );
};

export default Login;