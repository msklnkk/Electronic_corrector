// src/App.tsx
import React, { useState, useMemo } from "react";
import { ThemeProvider, CssBaseline } from "@mui/material";
import { Routes, Route } from "react-router-dom";
import { SnackbarProvider } from "notistack";

import { createAppTheme } from "./assets/styles/theme";
import { Header, Footer } from "./components/common";
import { ProtectedRoute } from "./components/auth";

import Welcome from "./pages/Welcome";
import Login from "./pages/Login";
import CheckDocument from "./pages/CheckDocument";
import CheckResult from "./pages/CheckResult";
import CustomCheck from "./pages/CustomCheck";
import CustomCheckResult from "./pages/CustomCheckResult";
import UserTemplateCheck from "./pages/UserTemplateCheck";
import UserTemplateResult from "./pages/UserTemplateResult";
import Profile from "./pages/Profile";
import EditProfile from "./pages/EditProfile";

import { ROUTES } from "./config/constants";

function App() {
  const [mode, setMode] = useState<"light" | "dark">("dark");
  const theme = useMemo(() => createAppTheme(mode), [mode]);

  const toggleTheme = () => {
    setMode((prev) => (prev === "light" ? "dark" : "light"));
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <SnackbarProvider
        maxSnack={3}
        anchorOrigin={{
          vertical: "top",
          horizontal: "right",
        }}
        autoHideDuration={4000}
        style={{
          marginTop: "80px",
        }}
      >
        <Header mode={mode} onThemeToggle={toggleTheme} />

        <Routes>
          {/* Публичные роуты */}
          <Route path={ROUTES.HOME} element={<Welcome />} />
          <Route path={ROUTES.LOGIN} element={<Login />} />

          {/* Защищённые роуты */}
          <Route
            path={ROUTES.CHECK}
            element={
              <ProtectedRoute>
                <CheckDocument />
              </ProtectedRoute>
            }
          />

          <Route
            path="/gost-check/result/:id"
            element={
              <ProtectedRoute>
                <CheckResult />
              </ProtectedRoute>
            }
          />

          <Route
            path={ROUTES.CUSTOM_CHECK}
            element={
              <ProtectedRoute>
                <CustomCheck />
              </ProtectedRoute>
            }
          />

          <Route
            path={ROUTES.CUSTOM_CHECK_RESULT}
            element={
              <ProtectedRoute>
                <CustomCheckResult />
              </ProtectedRoute>
            }
          />

          <Route
            path={ROUTES.USER_TEMPLATE_CHECK}
            element={
              <ProtectedRoute>
                <UserTemplateCheck />
              </ProtectedRoute>
            }
          />

          <Route
            path={ROUTES.USER_TEMPLATE_CHECK_RESULT}
            element={
              <ProtectedRoute>
                <UserTemplateResult />
              </ProtectedRoute>
            }
          />

          <Route
            path={ROUTES.PROFILE}
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />

          <Route
            path="/profile/edit"
            element={
              <ProtectedRoute>
                <EditProfile />
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Welcome />} />
        </Routes>

        <Footer />
      </SnackbarProvider>
    </ThemeProvider>
  );
}

export default App;