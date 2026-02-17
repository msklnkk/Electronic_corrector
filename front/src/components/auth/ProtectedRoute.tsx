// src/components/auth/ProtectedRoute.tsx
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { useAuth } from 'hooks';           // ← алиас

interface Props {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<Props> = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px', fontSize: '1.2rem' }}>
        Загрузка...
      </div>
    );
  }

  if (user?.loggedIn) {
    return <>{children}</>;
  }

  return (
    <Navigate
      to="/login"
      replace
      state={{ from: location.pathname }}
    />
  );
};