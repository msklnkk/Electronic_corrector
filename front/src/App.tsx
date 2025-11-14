// src/App.tsx
import React, { useState, useMemo } from "react";
import { ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import { Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Welcome from "./pages/Welcome";
import CheckDocumentPage from "./pages/CheckDocument";
import Login from "./pages/Login"; // ДОБАВИЛ
import { ProtectedRoute } from "./components/ProtectedRoute"; // ДОБАВИЛ


function App() {
  const [mode, setMode] = useState<"light" | "dark">("dark");

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: { main: "#8b5cf6" },
          background: {
            default: mode === "dark" ? "#0f172a" : "#f8fafc",
            paper: mode === "dark" ? "#1e293b" : "#ffffff",
          },
          text: {
            primary: mode === "dark" ? "#f8fafc" : "#1e293b",
            secondary: mode === "dark" ? "#cbd5e1" : "#475569",
          },
        },
        typography: {
          fontFamily: "'Inter', 'Roboto', sans-serif",
        },
      }),
    [mode]
  );

  const handleThemeToggle = () => {
    setMode((prev) => (prev === "light" ? "dark" : "light"));
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Header mode={mode} onThemeToggle={handleThemeToggle} />
      <Routes>
        <Route path="/" element={<Welcome />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/check"
          element={
            <ProtectedRoute>
              <CheckDocumentPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Welcome />} />
      </Routes>
    </ThemeProvider>
  );
}

export default App;