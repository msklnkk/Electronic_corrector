import React, { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Box,
  Button,
  CircularProgress,
  Typography,
  useTheme,
} from "@mui/material";
import { StyledCard } from "components";

type TemplateResult = {
  document_id: number;
  filename?: string;
  status: string;
  score: number;
  is_compliant: boolean;
  errors: string[];
  warnings: string[];
  total_checks: number;
  passed_checks: number;
};

type LocationState = {
  result?: TemplateResult;
  elapsedMs?: number;
};

type IssueRow = {
  type: string;
  description: string;
  priority: string;
};

const UserTemplateResult: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();

  const state = (location.state || {}) as LocationState;
  const result = state.result ?? null;
  const elapsedMs = state.elapsedMs ?? null;

  useEffect(() => {
    if (!result?.document_id || !elapsedMs) return;
    const diffSeconds = elapsedMs / 1000;
    if (!Number.isFinite(diffSeconds) || diffSeconds <= 0) return;
    try {
      const raw = localStorage.getItem("checkAnalysisTimes");
      const parsed: Record<string, number> = raw ? JSON.parse(raw) : {};
      const key = `user_template_${result.document_id}_${Date.now()}`;
      parsed[key] = diffSeconds;
      localStorage.setItem("checkAnalysisTimes", JSON.stringify(parsed));
    } catch { /* ignore */ }
  }, [result, elapsedMs]);

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
  const rawScore = result.score ?? 0;
  const normalizedScore = Math.min(Math.max(rawScore / 10, 0), 10);
  const percent = Math.round(rawScore);

  const statusText =
    normalizedScore >= 8
      ? "Хорошо"
      : normalizedScore >= 5
      ? "Удовлетворительно"
      : "Требует внимания";

  const formatTime = (ms: number): string => {
    if (ms < 1000) return `${ms} мс`;
    const s = Math.round(ms / 1000);
    if (s < 60) return `${s} сек`;
    const m = Math.floor(s / 60);
    return `${m} мин ${s % 60} сек`;
  };

  const analysisTime = elapsedMs !== null ? formatTime(elapsedMs) : "-";

  const issues: IssueRow[] = [
    ...result.errors.map((d) => ({ type: "Ошибка", description: d, priority: "Критично" })),
    ...result.warnings.map((d) => ({ type: "Замечание", description: d, priority: "Средний" })),
  ];

  const recommendation =
    normalizedScore >= 8
      ? "Документ соответствует заданным параметрам. Можно сдавать."
      : normalizedScore >= 5
      ? "Есть важные несоответствия. Рекомендуется исправить перед сдачей."
      : "Документ значительно не соответствует заданному шаблону.";

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

      <Box sx={{ display: "flex", flexDirection: { xs: "column", lg: "row" }, gap: 4 }}>
        {/* LEFT */}
        <Box sx={{ flex: 3, display: "flex", flexDirection: "column", gap: 4 }}>
          <StyledCard>
            <Typography variant="h6" mb={3}>
              Общая оценка (пользовательский шаблон)
            </Typography>

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
                  Соответствие шаблону: {normalizedScore.toFixed(1)}/10 ({percent}%)
                </Typography>
                <Typography color="text.secondary" mt={1}>
                  {result.status}
                </Typography>
                <Box sx={{ display: "flex", gap: 2, mt: 3, flexWrap: "wrap" }}>
                  <Box sx={badgeStyle(theme, "#2ecc71")}>{statusText}</Box>
                  <Box sx={badgeStyle(theme, "#e74c3c")}>{result.errors.length} критичных</Box>
                  <Box sx={badgeStyle(theme, "#f1c40f")}>{result.warnings.length} замечаний</Box>
                </Box>
              </Box>
            </Box>
          </StyledCard>

          <StyledCard>
            <Typography variant="h6" mb={2}>
              Найденные нарушения
            </Typography>

            <Box sx={tableHeader}>
              <span>Тип</span>
              <span>Описание</span>
              <span>Приоритет</span>
            </Box>

            {issues.length === 0 ? (
              <Box sx={{ opacity: 0.7, py: 2 }}>Нарушений не найдено 🎉</Box>
            ) : (
              issues.map((e, i) => (
                <Box key={i} sx={tableRow}>
                  <span>{e.type}</span>
                  <span>{e.description}</span>
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
        </Box>

        {/* RIGHT */}
        <Box sx={{ flex: 1, display: "flex", flexDirection: "column", gap: 4 }}>
          <StyledCard>
            <Typography variant="h6" mb={2}>
              Анализ завершен
            </Typography>
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
  gridTemplateColumns: "90px 1fr 120px",
  opacity: 0.6,
  padding: "12px 0",
  borderBottom: (theme: any) => `1px solid ${theme.palette.divider}`,
};

const tableRow = {
  display: "grid",
  gridTemplateColumns: "90px 1fr 120px",
  padding: "14px 0",
  borderBottom: (theme: any) => `1px solid ${theme.palette.divider}`,
};

const InfoRow = ({
  label,
  value,
  green = false,
}: {
  label: string;
  value: string | number;
  green?: boolean;
}) => (
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

export default UserTemplateResult;
