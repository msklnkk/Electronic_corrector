// src/pages/CheckResult.tsx
import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api"; 
import {
  Button,
  Box,
  Typography,
  CircularProgress,
  Alert,
  useTheme,
} from "@mui/material";
import { useSnackbar } from "notistack";
import { API_ROUTES } from "../config/constants";  
import { StyledCard, GradientButton } from "components";

type IssueRow = {
  type: string;
  category: string;
  description: string;
  page: string | number;
  priority: string;
};

const CheckResult: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();

  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchResult = useCallback(async () => {
    console.log("CheckResult: Запуск fetchResult для check_id =", id);

    if (!id) {
      enqueueSnackbar("ID проверки не найден", { variant: "error" });
      setError("ID проверки не найден");
      setLoading(false);
      return;
    }

    try {
      console.log("CheckResult: Делаю запрос GET", API_ROUTES.DOCUMENTS.CHECK_RESULT(id));
      const res = await api.get(API_ROUTES.DOCUMENTS.CHECK_RESULT(id));
      const data = res.data || {};

      console.log("CheckResult: Получен ответ от бэкенда:", data);

      // Если вдруг попали сюда напрямую по URL и проверка еще идет
      const isProcessing =
        data?.status === "Анализируется" ||
        data?.status === "analyzing" ||
        (data?.total_checks === 0 && data?.passed_checks === 0 && !data?.errors?.length);

      if (isProcessing) {
        console.log("CheckResult: Проверка еще идет - повтор через 3 сек");
        setTimeout(fetchResult, 3000);
        return; // не убираем loading пока не готово
      }

      setResult(data);
      setLoading(false);

    } catch (err: any) {
      console.error("CheckResult: Ошибка при получении результата:", err.response || err);
      const errorMsg = err.response?.data?.detail || "Не удалось загрузить результат";
      enqueueSnackbar(errorMsg, { variant: "error" });
      setError(errorMsg);
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchResult();
  }, [fetchResult]);

  // ─── РЕНДЕР ────────────────────────────────────────────────

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 3,
        }}
      >
        <CircularProgress size={80} thickness={4} sx={{ color: "primary.main" }} />
        <Typography variant="h5" fontWeight={700}>
          Загружаем результат...
        </Typography>
        <Typography variant="body2" sx={{ opacity: 0.5 }}>
          Пожалуйста, подождите
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ textAlign: "center", py: 10 }}>
        <Typography variant="h6" color="error">{error}</Typography>
        <Button variant="contained" onClick={() => navigate(-1)} sx={{ mt: 3 }}>
          Назад
        </Button>
      </Box>
    );
  }

  if (!result) {
    return (
      <Box sx={{ textAlign: "center", py: 10 }}>
        <Typography variant="h6">Результат проверки не найден</Typography>
        <Button variant="contained" onClick={() => navigate(-1)} sx={{ mt: 3 }}>
          Назад
        </Button>
      </Box>
    );
  }

  const cleanFilename = (name?: string) => {
    if (!name) return "Документ";
    return name.replace(/^\d+_[a-f0-9]+_/, "") || "Документ";
  };

  const documentName = cleanFilename(result.filename);

  const rawScore = result.score ?? "0";
  const score =
    typeof rawScore === "string"
      ? Number(rawScore.replace(/^0+/, "")) || 0
      : Number(rawScore);

  const percent = Math.min(Math.max(score, 0), 100);
  const normalizedScore = percent / 10;  // для отображения X/10
  const statusText = percent >= 80 ? "Хорошо" : percent >= 50 ? "Удовлетворительно" : "Требует внимания";

  const backendErrors: string[] = Array.isArray(result.errors) ? result.errors : [];
  const backendWarnings: string[] = Array.isArray(result.warnings) ? result.warnings : [];

  const criticalCount = backendErrors.length;
  const warningCount = backendWarnings.length;

  const issues: IssueRow[] = [
    ...backendErrors.map((text) => ({
      type: "Ошибка",
      category: "ГОСТ",
      description: text,
      page: "-",
      priority: "Критично",
    })),
    ...backendWarnings.map((text) => ({
      type: "Замечание",
      category: "ГОСТ",
      description: text,
      page: "-",
      priority: "Средний",
    })),
  ];

  const analysisTime =
    result.analysis_time ||
    (typeof result.analysis_time_ms === "number"
      ? `${(result.analysis_time_ms / 1000).toFixed(1)} сек`
      : "-");

  const pagesChecked = result.pages_checked ?? "-";
  const accuracy = result.accuracy ?? "-";

  const recommendation =
    result.recommendation ||
    (normalizedScore >= 8
      ? "Документ оформлен хорошо. Можно сдавать."
      : normalizedScore >= 5
      ? "Есть важные замечания. Лучше исправить перед сдачей."
      : "Документ сильно не соответствует ГОСТ. Требуется доработка.");

  return (
    <Box
      sx={{
        minHeight: "100vh",
        px: { xs: 2, md: 8 },
        py: 6,
      }}
    >
      <Typography
        sx={{ 
          cursor: "pointer", 
          opacity: 0.6, 
          mb: 2,
          '&:hover': { opacity: 1 }
        }}
        onClick={() => navigate(-1)}
      >
        ← Вернуться назад
      </Typography>

      <Typography variant="h4" fontWeight={700} mb={4}>
        Результаты проверки • {documentName}
      </Typography>

      {/* Статус и ошибки */}
      <Box sx={{ mb: 4 }}>
        <Typography 
          variant="h6" 
          color={result.score === "0.0" ? "warning.main" : "success.main"}
        >
          Статус: {result.status || "Неизвестно"}
        </Typography>

        {result.report?.results?.length > 0 && (
          <Alert severity="error" sx={{ mt: 2 }}>
            <Typography variant="subtitle1">Обнаружены ошибки при проверке:</Typography>
            {result.report.results.map((r: any, idx: number) => (
              <Typography key={idx} sx={{ mt: 1 }}>
                {r.message} (severity: {r.severity})
              </Typography>
            ))}
          </Alert>
        )}
      </Box>

      <Box sx={{ display: "flex", flexDirection: { xs: 'column', lg: 'row' }, gap: 4 }}>
        {/* LEFT */}
        <Box sx={{ flex: 3, display: "flex", flexDirection: "column", gap: 4 }}>
          <StyledCard>
            <Typography variant="h6" mb={3}>
              Общая оценка
            </Typography>

            <Box sx={{ display: "flex", alignItems: "center", gap: 6, flexWrap: 'wrap' }}>
              <Box sx={{ position: "relative" }}>
                <CircularProgress
                  variant="determinate"
                  value={(normalizedScore / 10) * 100}
                  size={160}
                  thickness={6}
                  sx={{
                    color: theme.palette.primary.main,
                    "& .MuiCircularProgress-circle": { strokeLinecap: "round" },
                  }}
                />
                <Typography
                  sx={{
                    position: "absolute",
                    top: "50%",
                    left: "50%",
                    transform: "translate(-50%,-50%)",
                    fontSize: 42,
                    fontWeight: 700,
                  }}
                >
                  {normalizedScore.toFixed(1)}
                </Typography>
              </Box>

              <Box>
                <Typography variant="h5" fontWeight={600}>
                  Соответствие ГОСТ: {normalizedScore.toFixed(1)}/10 ({percent}%)
                </Typography>
                <Typography color="text.secondary" mt={1}>
                  {result.status || "Результат проверки"}
                </Typography>

                <Box sx={{ display: "flex", gap: 2, mt: 3, flexWrap: 'wrap' }}>
                  <Box sx={badgeStyle(theme, "#2ecc71")}>{statusText}</Box>
                  <Box sx={badgeStyle(theme, "#e74c3c")}>{criticalCount} критичных</Box>
                  <Box sx={badgeStyle(theme, "#f1c40f")}>{warningCount} замечаний</Box>
                </Box>
              </Box>
            </Box>
          </StyledCard>

          <StyledCard>
            <Typography variant="h6" mb={2}>
              Найденные ошибки и замечания
            </Typography>

            <Box sx={tableHeader}>
              <span>Тип</span>
              <span>Категория</span>
              <span>Описание</span>
              <span>Страница</span>
              <span>Приоритет</span>
            </Box>

            {issues.length === 0 ? (
              <Box sx={{ opacity: 0.7, py: 2 }}>Ошибок не найдено 🎉</Box>
            ) : (
              issues.map((e, i) => (
                <Box key={i} sx={tableRow}>
                  <span>{e.type}</span>
                  <span>{e.category}</span>
                  <span>{e.description}</span>
                  <span>{e.page}</span>
                  <span
                    style={{
                      color: e.priority === "Критично" ? "#ff7675" : "#f1c40f",
                      fontWeight: 600,
                    }}
                  >
                    {e.priority}
                  </span>
                </Box>
              ))
            )}
          </StyledCard>

          <Box sx={{ display: "flex", gap: 3, flexWrap: 'wrap' }}>
            <GradientButton color="purple">Скачать отчет в PDF</GradientButton>
            <GradientButton color="cyan">Исправить документ</GradientButton>
          </Box>
        </Box>

        {/* RIGHT */}
        <Box sx={{ flex: 1, display: "flex", flexDirection: "column", gap: 4 }}>
          <StyledCard>
            <Typography variant="h6" mb={2}>
              ИИ анализ завершен
            </Typography>

            <InfoRow label="Время анализа" value={analysisTime} />
            <InfoRow label="Страниц проверено" value={pagesChecked} />
            <InfoRow label="Точность анализа" value={`${accuracy}%`} green />
          </StyledCard>

          <Box
            sx={{
              p: 4,
              borderRadius: "18px",
              background: "linear-gradient(135deg, #6C3BFF, #9C27B0)",
              color: "white",
            }}
          >
            <Typography variant="h6">Рекомендация</Typography>
            <Typography mt={2}>{recommendation}</Typography>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

const badgeStyle = (theme: any, color: string) => ({
  background: theme.palette.mode === 'dark' ? `${color}22` : `${color}11`,
  color,
  px: 2,
  py: 0.6,
  borderRadius: "8px",
  fontSize: 14,
  fontWeight: 600,
});

const tableHeader = {
  display: "grid",
  gridTemplateColumns: "80px 160px 1fr 100px 120px",
  opacity: 0.6,
  padding: "12px 0",
  borderBottom: (theme: any) => `1px solid ${theme.palette.divider}`,
};

const tableRow = {
  display: "grid",
  gridTemplateColumns: "80px 160px 1fr 100px 120px",
  padding: "14px 0",
  borderBottom: (theme: any) => `1px solid ${theme.palette.divider}`,
};

const InfoRow = ({ label, value, green = false }: { label: string; value: string | number; green?: boolean }) => (
  <Box
    sx={{
      display: "flex",
      justifyContent: "space-between",
      py: 1.5,
      borderBottom: (theme: any) => `1px solid ${theme.palette.divider}`,
    }}
  >
    <Typography color="text.secondary">{label}</Typography>
    <Typography color={green ? "success.main" : "text.primary"} fontWeight={600}>
      {value}
    </Typography>
  </Box>
);

export default CheckResult;