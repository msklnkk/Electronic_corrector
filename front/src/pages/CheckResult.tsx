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
import { GlobalLoader } from "components";
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
  const [documentInfo, setDocumentInfo] = useState<any>(null);
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

      setResult(data);

      // Получаем информацию о документе для времени загрузки
      if (data.document_id) {
        try {
          const docRes = await api.get(API_ROUTES.DOCUMENTS.FULL_INFO(data.document_id));
          console.log("CheckResult: Информация о документе:", docRes.data);
          setDocumentInfo(docRes.data);
        } catch (err) {
          console.error("CheckResult: Ошибка при получении информации о документе:", err);
        }
      }

      setLoading(false);

      // Повторяем запрос, если проверка ещё идёт
      if (data?.status === "Анализируется" || data?.status === "processing" || data?.score === "0.0" || !data?.score) {
        console.log("CheckResult: Проверка в процессе — повтор через 3 сек");
        setTimeout(fetchResult, 3000);
      }
    } catch (err: any) {
      console.error("CheckResult: Ошибка при получении результата:", err.response || err);
      const errorMsg = err.response?.data?.detail || "Не удалось загрузить результат";
      enqueueSnackbar(errorMsg, { variant: "error" });
      setError(errorMsg);
      setLoading(false);
    }
  }, [id, enqueueSnackbar]);

  useEffect(() => {
    fetchResult();
  }, [fetchResult]);

  // ✅ Сохраняем фактическое время проверки в localStorage,
  // чтобы потом можно было посчитать среднее в профиле
  useEffect(() => {
    if (!result?.check_id || !result?.checked_at || !documentInfo?.upload_datetime) {
      return;
    }

    try {
      const checkedAt = new Date(result.checked_at);
      const uploadedAt = new Date(documentInfo.upload_datetime);
      const diffSeconds = Math.max(
        (checkedAt.getTime() - uploadedAt.getTime()) / 1000,
        0
      );

      if (!Number.isFinite(diffSeconds) || diffSeconds === 0) {
        return;
      }

      const storageKey = "checkAnalysisTimes";
      const raw = localStorage.getItem(storageKey);
      const parsed: Record<string, number> = raw ? JSON.parse(raw) : {};

      // Не дублируем одно и то же измерение по check_id
      if (!parsed[result.check_id]) {
        parsed[result.check_id] = diffSeconds;
        localStorage.setItem(storageKey, JSON.stringify(parsed));
      }
    } catch (e) {
      console.error("Ошибка сохранения времени анализа в localStorage:", e);
    }
  }, [result, documentInfo]);

  // Вычисление времени проверки
  const calculateAnalysisTime = (): string => {
    if (!result?.checked_at || !documentInfo?.upload_datetime) {
      return "-";
    }

    try {
      const checkedAt = new Date(result.checked_at);
      const uploadedAt = new Date(documentInfo.upload_datetime);
      
      const diffMs = checkedAt.getTime() - uploadedAt.getTime();
      
      // Если меньше 1 секунды - показываем миллисекунды
      if (diffMs < 1000) {
        return `${diffMs} мс`;
      }
      
      const diffSeconds = Math.round(diffMs / 1000);

      // Если меньше минуты - показываем секунды
      if (diffSeconds < 60) {
        return `${diffSeconds} сек`;
      } 
      
      // Если меньше часа - показываем минуты и секунды
      if (diffSeconds < 3600) {
        const minutes = Math.floor(diffSeconds / 60);
        const seconds = diffSeconds % 60;
        return `${minutes} мин ${seconds} сек`;
      } 
      
      // Если больше часа - показываем часы и минуты
      const hours = Math.floor(diffSeconds / 3600);
      const minutes = Math.floor((diffSeconds % 3600) / 60);
      return `${hours} ч ${minutes} мин`;
    } catch (err) {
      console.error("Ошибка вычисления времени:", err);
      return "-";
    }
  };

  // ─── РЕНДЕР ────────────────────────────────────────────────

  if (loading) {
    return (
      <GlobalLoader 
        open={loading} 
        message="Проверка документа... Это может занять несколько секунд" 
      />
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

  const normalizedScore = Math.min(Math.max(score, 0), 10);
  const percent = Math.round((normalizedScore / 10) * 100);

  const statusText = normalizedScore >= 8 ? "Хорошо" : "Требует внимания";

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

  // ✅ Используем вычисленное время
  const analysisTime = calculateAnalysisTime();
  const pagesChecked = result.pages_checked ?? "-";
  const accuracy = result.accuracy ?? 95;

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
              Анализ завершен
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