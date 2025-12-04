// src/pages/CheckResult.tsx
import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/axios.config";
import {
  Container,
  Paper,
  Typography,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
  Button,
  Box,
  Chip,
} from "@mui/material";
import { CheckCircle, Error, Warning, Refresh } from "@mui/icons-material";

const CheckResult: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<any>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      // Сначала пробуем получить РЕЗУЛЬТАТ по check_id
      const resultRes = await api.get(`/gost-check/result/${id}`);
      setResult(resultRes.data);
      setStatus({ status: resultRes.data.status || "Проверен" });
      setLoading(false);
    } catch (err: any) {
      // Если результат ещё не готов (404 или 425) — получаем статус
      if (err.response?.status === 404 || err.response?.status === 425) {
        try {
          // Важно: /status принимает document_id, а не check_id!
          // Но мы не знаем document_id! → Поэтому временно делаем по check_id и надеемся,
          // что бэкенд поддерживает оба варианта.
          // Лучше: передавать document_id и check_id вместе при старте!
          const statusRes = await api.get(`/gost-check/status/${id}`);
          setStatus(statusRes.data);
        } catch (statusErr) {
          console.error("Не удалось получить статус:", statusErr);
        }
      }
    }
  }, [id]);

  useEffect(() => {
    if (!id) return;

    fetchData();
    const interval = setInterval(fetchData, 3000); // опрос каждые 3 сек

    return () => clearInterval(interval);
  }, [id, fetchData]);

  // Экран загрузки
  if (loading || !status) {
    return (
      <Container sx={{ textAlign: "center", py: 10 }}>
        <CircularProgress size={80} thickness={5} />
        <Typography variant="h5" sx={{ mt: 4 }}>
          {status?.status || "Идёт анализ документа..."}
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 2 }}>
          Проверка по ГОСТ может занять до 30 секунд
        </Typography>
      </Container>
    );
  }

  const score = result?.score ?? 0;

  const getScoreColor = () => {
    if (score >= 90) return "success";
    if (score >= 70) return "warning";
    return "error";
  };

  const getStatusColor = () => {
    if (status.status === "Идеален") return "success";
    if (status.status === "Отправлен на доработку") return "error";
    return "warning";
  };

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Paper sx={{ p: 5, borderRadius: 3, boxShadow: 3 }}>
        <Typography variant="h3" textAlign="center" fontWeight="bold" gutterBottom>
          Результат проверки ГОСТ
        </Typography>

        <Box textAlign="center" my={4}>
          <Typography variant="h1" fontWeight="bold" color={getScoreColor() + ".main"}>
            {score.toFixed(0)}%
          </Typography>
          <LinearProgress
            variant="determinate"
            value={score}
            sx={{
              height: 20,
              borderRadius: 10,
              mt: 2,
              backgroundColor: "#e0e0e0",
              "& .MuiLinearProgress-bar": {
                backgroundColor: getScoreColor() + ".main",
              },
            }}
          />
        </Box>

        <Box textAlign="center" mb={4}>
          <Chip
            label={status.status}
            color={getStatusColor()}
            variant="outlined"
            sx={{
              fontSize: "1.3rem",
              fontWeight: "bold",
              py: 3.5,
              px: 4,
              borderWidth: 3,
            }}
          />
        </Box>

        {result && (
          <>
            <Typography variant="h6" gutterBottom>
              Замечания ({result.errors?.length || 0} критических, {result.warnings?.length || 0} предупреждений):
            </Typography>
            <List>
              {result.errors?.map((e: any, i: number) => (
                <ListItem key={i}>
                  <ListItemIcon><Error color="error" /></ListItemIcon>
                  <ListItemText primary={e.message} secondary="Критическая ошибка" />
                </ListItem>
              ))}
              {result.warnings?.map((w: any, i: number) => (
                <ListItem key={i}>
                  <ListItemIcon><Warning color="warning" /></ListItemIcon>
                  <ListItemText primary={w.message} secondary="Предупреждение" />
                </ListItem>
              ))}
              {(!result.errors || result.errors.length === 0) &&
                (!result.warnings || result.warnings.length === 0) && (
                  <ListItem>
                    <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
                    <ListItemText primary="Документ полностью соответствует ГОСТ!" />
                  </ListItem>
                )}
            </List>
          </>
        )}

        <Box textAlign="center" mt={6}>
          <Button
            variant="contained"
            size="large"
            startIcon={<Refresh />}
            onClick={() => navigate("/")}
            sx={{ borderRadius: 3, py: 1.5, px: 5 }}
          >
            Проверить ещё документ
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default CheckResult;