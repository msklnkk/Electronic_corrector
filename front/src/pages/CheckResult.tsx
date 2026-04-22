// src/pages/CheckResult.tsx — только для ГОСТ-проверок
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
import { StyledCard } from "components";

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
    if (!id) {
      enqueueSnackbar("ID проверки не найден", { variant: "error" });
      setError("ID проверки не найден");
      setLoading(false);
      return;
    }

    try {
      const res = await api.get(API_ROUTES.DOCUMENTS.CHECK_RESULT(id));
      const data = res.data || {};
      setResult(data);

      if (data.document_id) {
        try {
          const docRes = await api.get(API_ROUTES.DOCUMENTS.FULL_INFO(data.document_id));
          setDocumentInfo(docRes.data);
        } catch (err) {
          console.error("CheckResult: Ошибка при получении информации о документе:", err);
        }
      }

      setLoading(false);

      if (data?.status === "Анализируется" || data?.status === "processing" || !data?.score) {
        setTimeout(fetchResult, 3000);
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || "Не удалось загрузить результат";
      enqueueSnackbar(errorMsg, { variant: "error" });
      setError(errorMsg);
      setLoading(false);
    }
  }, [id, enqueueSnackbar]);

  useEffect(() => {
    fetchResult();
  }, [fetchResult]);

  // Сохраняем время проверки в localStorage для статистики профиля
  useEffect(() => {
    if (!result?.check_id || !result?.checked_at || !documentInfo?.upload_datetime) return;

    try {
      const checkedAt = new Date(result.checked_at);
      const uploadedAt = new Date(documentInfo.upload_datetime);
      const diffSeconds = Math.max((checkedAt.getTime() - uploadedAt.getTime()) / 1000, 0);

      if (!Number.isFinite(diffSeconds) || diffSeconds === 0) return;

      const raw = localStorage.getItem("checkAnalysisTimes");
      const parsed: Record<string, number> = raw ? JSON.parse(raw) : {};
      if (!parsed[result.check_id]) {
        parsed[result.check_id] = diffSeconds;
        localStorage.setItem("checkAnalysisTimes", JSON.stringify(parsed));
      }
    } catch (e) {
      console.error("Ошибка сохранения времени анализа:", e);
    }
  }, [result, documentInfo]);

  const calculateAnalysisTime = (): string => {
    const fmt = (ms: number): string => {
      if (ms < 1000) return `${ms} мс`;
      const s = Math.round(ms / 1000);
      if (s < 60) return `${s} сек`;
      if (s < 3600) return `${Math.floor(s / 60)} мин ${s % 60} сек`;
      return `${Math.floor(s / 3600)} ч ${Math.floor((s % 3600) / 60)} мин`;
    };

    if (!result?.checked_at || !documentInfo?.upload_datetime) return "-";
    try {
      const diff = new Date(result.checked_at).getTime() - new Date(documentInfo.upload_datetime).getTime();
      return fmt(Math.max(diff, 0));
    } catch {
      return "-";
    }
  };

  if (loading) {
    return <GlobalLoader open={loading} message="Проверка документа... Это может занять несколько секунд" />;
  }

  if (error) {
    return (
      <Box sx={{ textAlign: "center", py: 10 }}>
        <Typography variant="h6" color="error">{error}</Typography>
        <Button variant="contained" onClick={() => navigate(-1)} sx={{ mt: 3 }}>Назад</Button>
      </Box>
    );
  }

  if (!result) {
    return (
      <Box sx={{ textAlign: "center", py: 10 }}>
        <Typography variant="h6">Результат проверки не найден</Typography>
        <Button variant="contained" onClick={() => navigate(-1)} sx={{ mt: 3 }}>Назад</Button>
      </Box>
    );
  }

  const cleanFilename = (name?: string) => {
    if (!name) return "Документ";
    return name.replace(/^\d+_[a-f0-9]+_/, "") || "Документ";
  };

  const documentName = cleanFilename(result.filename);

  // score из БД — целое число 0-100, переводим в 0-10 для отображения
  const rawScore = Number(result.score ?? 0);
  const normalizedScore = Math.min(Math.max(rawScore / 10, 0), 10);
  const percent = Math.round(rawScore);

  const statusText = normalizedScore >= 8 ? "Хорошо" : "Требует внимания";

  const backendErrors: string[] = Array.isArray(result.errors) ? result.errors : [];
  const backendWarnings: string[] = Array.isArray(result.warnings) ? result.warnings : [];

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

  const analysisTime = calculateAnalysisTime();
  const pagesChecked = result.pages_checked ?? result.total_pages ?? "-";

  const recommendation =
    result.short_recommendation ||
    result.recommendation ||
    (normalizedScore >= 8
      ? "Документ оформлен хорошо. Можно сдавать."
      : normalizedScore >= 5
      ? "Есть важные замечания. Лучше исправить перед сдачей."
      : "Документ сильно не соответствует ГОСТ. Требуется доработка.");

  return (
    <Box sx={{ minHeight: "100vh", px: { xs: 2, md: 8 }, py: 6 }}>
      <Typography
        sx={{ cursor: "pointer", opacity: 0.6, mb: 2, "&:hover": { opacity: 1 } }}
        onClick={() => navigate(-1)}
      >
        ← Вернуться назад
      </Typography>

      <Typography variant="h4" fontWeight={700} mb={4}>
        Результаты проверки • {documentName}
      </Typography>

      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" color={rawScore === 0 ? "warning.main" : "success.main"}>
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

      <Box sx={{ display: "flex", flexDirection: { xs: "column", lg: "row" }, gap: 4 }}>
        {/* LEFT */}
        <Box sx={{ flex: 3, display: "flex", flexDirection: "column", gap: 4 }}>
          <StyledCard>
            <Typography variant="h6" mb={3}>Общая оценка</Typography>

            <Box sx={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
              <Box sx={{ position: "relative" }}>
                <CircularProgress
                  variant="determinate"
                  value={percent}
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

                <Box sx={{ display: "flex", gap: 2, mt: 3, flexWrap: "wrap" }}>
                  <Box sx={badgeStyle(theme, "#2ecc71")}>{statusText}</Box>
                  <Box sx={badgeStyle(theme, "#e74c3c")}>{backendErrors.length} критичных</Box>
                  <Box sx={badgeStyle(theme, "#f1c40f")}>{backendWarnings.length} замечаний</Box>
                </Box>
              </Box>
            </Box>
          </StyledCard>

          <StyledCard>
            <Typography variant="h6" mb={2}>Найденные ошибки и замечания</Typography>

            <Box sx={tableHeader}>
              <span>Тип</span>
              <span>Категория</span>
              <span>Описание</span>
              <span>Приоритет</span>
            </Box>

            {issues.length === 0 ? (
              <Box sx={{ opacity: 0.7, py: 2 }}>Ошибок не найдено 🎉</Box>
            ) : (
              issues.map((e, i) => (
                <Box key={i} sx={tableRow}>
                  <span>{e.type}</span>
                  <span>{e.category}</span>
                  <span style={{ overflowWrap: "break-word", wordBreak: "break-word", minWidth: 0 }}>{e.description}</span>
                  <span style={{ color: e.priority === "Критично" ? "#ff7675" : "#f1c40f", fontWeight: 600 }}>
                    {e.priority}
                  </span>
                </Box>
              ))
            )}
          </StyledCard>
        </Box>

        {/* RIGHT */}
        <Box sx={{ flex: 1, display: "flex", flexDirection: "column", gap: 4 }}>
          <StyledCard>
            <Typography variant="h6" mb={2}>Анализ завершен</Typography>
            <InfoRow label="Время анализа" value={analysisTime} />
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
  background: theme.palette.mode === "dark" ? `${color}22` : `${color}11`,
  color,
  px: 2,
  py: 0.6,
  borderRadius: "8px",
  fontSize: 14,
  fontWeight: 600,
});

const tableHeader = {
  display: "grid",
  gridTemplateColumns: "120px 160px 1fr 120px",
  columnGap: "16px",
  opacity: 0.6,
  padding: "12px 0",
  borderBottom: (theme: any) => `1px solid ${theme.palette.divider}`,
};

const tableRow = {
  display: "grid",
  gridTemplateColumns: "120px 160px 1fr 120px",
  columnGap: "16px",
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
