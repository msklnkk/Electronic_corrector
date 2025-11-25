// src/components/ProtectedRoute.tsx
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface Props {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<Props> = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation(); // ← получаем текущий путь

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px', fontSize: '1.2rem' }}>
        Загрузка...
      </div>
    );
  }

  // Если залогинен — показываем страницу
  if (user?.loggedIn) {
    return <>{children}</>;
  }

  // Если НЕ залогинен — редиректим на логин и запоминаем, откуда пришёл
  return (
    <Navigate
      to="/login"
      replace
      state={{ from: location.pathname }} // ← вот сюда сохраняем путь!
    />
  );
};