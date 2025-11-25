// src/App.tsx
import React, { useState, useMemo } from "react";
import { ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import { Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Welcome from "./pages/Welcome";
import CheckDocumentPage from "./pages/CheckDocument";
import Profile from "./pages/Profile";         
import { ProtectedRoute } from "./components/ProtectedRoute";
import Login from "./pages/Login";

function App() {
  const [mode, setMode] = useState<"light" | "dark">("dark");

  const theme = useMemo(() => createTheme({
    palette: {
      mode,
      primary: { main: "#8b5cf6" },
      background: {
        default: mode === "dark" ? "#0f172a" : "#f8fafc",
        paper: mode === "dark" ? "#1e293b" : "#ffffff",
      },
    },
    typography: { fontFamily: "'Inter', 'Roboto', sans-serif" },
  }), [mode]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Header mode={mode} onThemeToggle={() => setMode(m => m === "light" ? "dark" : "light")} />
      <Routes>
        <Route path="/" element={<Welcome />} />
        <Route path="/login" element={<Login />} />
        
        {/* Защищённые маршруты */}
        <Route
          path="/check"
          element={<ProtectedRoute><CheckDocumentPage /></ProtectedRoute>}
        />
        
        {/* СТРАНИЦА ПРОФИЛЯ */}
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<Welcome />} />
      </Routes>
    </ThemeProvider>
  );
}

export default App;