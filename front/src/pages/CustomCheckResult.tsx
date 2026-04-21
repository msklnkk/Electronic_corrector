import React, { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Typography,
  useTheme,
} from "@mui/material";
import { StyledCard } from "components";

type Finding = {
  rule_code?: string | number | null;
  rule_title?: string;
  status: string;
  page?: number | null;
  location?: string;
  section?: string;
  problem?: string;
  evidence?: string;
  fix?: string;
  expected_value?: unknown;
  actual_value?: unknown;
};

type SemanticResult = {
  document_id: number;
  filename?: string;
  ruleset_code?: string;
  overall_score?: number;
  score_label?: string;
  status?: string;
  short_recommendation?: string;
  total_pages?: number;
  summary?: {
    total_checks?: number;
    passed_checks?: number;
    failed_checks?: number;
    warning_checks?: number;
    manual_checks?: number;
  };
  findings?: Finding[];
};

type LocationState = {
  resultType?: "semantic";
  semanticResult?: SemanticResult;
  elapsedMs?: number;
};

const CATEGORY_LABELS: Record<string, string> = {
  structure: "Структура",
  format: "Форматирование",
  references: "Список источников",
  content: "Содержание",
  appendices: "Приложения",
  title_page: "Титульный лист",
  introduction: "Введение",
  conclusion: "Заключение",
};

const CustomCheckResult: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();

  // Пытаемся восстановить из localStorage если state потерян (напр. после F5)
  const resolveState = (): LocationState => {
    const s = (location.state || {}) as LocationState;
    if (s.resultType === "semantic") return s;
    try {
      const history: Array<{ check_id: string }> = JSON.parse(
        localStorage.getItem("customCheckHistory") ?? "[]"
      );
      const first = history[0];
      if (first) {
        const raw = localStorage.getItem(`customResult_${first.check_id}`);
        if (raw) return JSON.parse(raw) as LocationState;
      }
    } catch { /* ignore */ }
    return s;
  };

  const state = resolveState();
  const result = state.resultType === "semantic" ? state.semanticResult : null;
  const elapsedMs = state.elapsedMs ?? null;

  useEffect(() => {
    if (!result || !elapsedMs || !result.document_id) return;
    const diffSeconds = elapsedMs / 1000;
    if (!Number.isFinite(diffSeconds) || diffSeconds <= 0) return;
    try {
      const raw = localStorage.getItem("checkAnalysisTimes");
      const parsed: Record<string, number> = raw ? JSON.parse(raw) : {};
      const key = `semantic_${result.document_id}`;
      if (!parsed[key]) {
        parsed[key] = diffSeconds;
        localStorage.setItem("checkAnalysisTimes", JSON.stringify(parsed));
      }
    } catch (e) {
      console.error("Ошибка сохранения времени анализа:", e);
    }
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

  // overall_score is 0-1 scale from backend
  const overallScore = result.overall_score ?? 0;
  const normalizedScore = Math.min(Math.max(overallScore * 10, 0), 10);
  const percent = Math.round(overallScore * 100);

  const formatTime = (ms: number): string => {
    if (ms < 1000) return `${ms} мс`;
    const s = Math.round(ms / 1000);
    if (s < 60) return `${s} сек`;
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${m} мин ${rem} сек`;
  };

  const analysisTime = elapsedMs !== null ? formatTime(elapsedMs) : "-";

  const findings: Finding[] = Array.isArray(result.findings) ? result.findings : [];
  const failed = findings.filter((f) => f.status === "failed");
  const warnings = findings.filter((f) => f.status === "warning");

  const summary = result.summary;
  const statusText = normalizedScore >= 8 ? "Хорошо" : normalizedScore >= 5 ? "Удовлетворительно" : "Требует внимания";

  const categoryLabel = (f: Finding) =>
    CATEGORY_LABELS[f.section ?? ""] || CATEGORY_LABELS[f.location ?? ""] || f.section || f.location || "Общее";

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
                {result.score_label && (
                  <Typography color="text.secondary" mt={1}>
                    {result.score_label}
                  </Typography>
                )}
                <Box sx={{ display: "flex", gap: 2, mt: 3, flexWrap: "wrap" }}>
                  <Chip label={statusText} color={normalizedScore >= 8 ? "success" : "warning"} />
                  <Chip label={`${failed.length} ошибок`} color="error" variant="outlined" />
                  <Chip label={`${warnings.length} замечаний`} color="warning" variant="outlined" />
                </Box>
              </Box>
            </Box>
          </StyledCard>

          {/* Findings */}
          <StyledCard>
            <Typography variant="h6" mb={3}>
              Найденные нарушения
            </Typography>

            {findings.length === 0 ? (
              <Typography sx={{ opacity: 0.7, py: 2 }}>Нарушений не найдено 🎉</Typography>
            ) : (
              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                {findings.map((f, i) => (
                  <Box
                    key={i}
                    sx={{
                      p: 2.5,
                      borderRadius: 2,
                      border: `1px solid`,
                      borderColor: f.status === "failed" ? "error.main" : "warning.main",
                      bgcolor: f.status === "failed"
                        ? theme.palette.mode === "dark" ? "rgba(255,99,71,0.08)" : "rgba(255,0,0,0.03)"
                        : theme.palette.mode === "dark" ? "rgba(255,193,7,0.08)" : "rgba(255,193,7,0.04)",
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1, flexWrap: "wrap" }}>
                      <Chip
                        label={f.status === "failed" ? "Ошибка" : "Замечание"}
                        color={f.status === "failed" ? "error" : "warning"}
                        size="small"
                      />
                      <Chip label={categoryLabel(f)} size="small" variant="outlined" />
                      {f.page != null && (
                        <Chip label={`стр. ${f.page}`} size="small" variant="outlined" />
                      )}
                      {f.rule_code != null && (
                        <Typography variant="caption" color="text.secondary">
                          Правило #{f.rule_code}
                        </Typography>
                      )}
                    </Box>

                    {f.rule_title && (
                      <Typography variant="subtitle2" fontWeight={600} mb={0.5}>
                        {f.rule_title}
                      </Typography>
                    )}

                    {f.problem && (
                      <Typography variant="body2" color="text.secondary" mb={0.5}>
                        {f.problem}
                      </Typography>
                    )}

                    {f.evidence && (
                      <Typography variant="body2" sx={{ fontStyle: "italic", opacity: 0.8, mb: 0.5 }}>
                        {f.evidence}
                      </Typography>
                    )}

                    {f.fix && (
                      <Box sx={{ mt: 1, p: 1.5, borderRadius: 1, bgcolor: theme.palette.mode === "dark" ? "rgba(46,204,113,0.15)" : "rgba(46,204,113,0.1)" }}>
                        <Typography variant="caption" fontWeight={700} color="success.main">
                          Как исправить:{" "}
                        </Typography>
                        <Typography variant="caption" color="success.main">
                          {f.fix}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                ))}
              </Box>
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
            <InfoRow label="Страниц проверено" value={result.total_pages ?? "-"} />
            {summary && (
              <>
                <InfoRow label="Всего проверок" value={summary.total_checks ?? "-"} />
                <InfoRow label="Пройдено" value={summary.passed_checks ?? "-"} green />
                <InfoRow label="Ошибок" value={summary.failed_checks ?? "-"} />
                <InfoRow label="Замечаний" value={summary.warning_checks ?? "-"} />
              </>
            )}
          </StyledCard>

          {result.short_recommendation && (
            <Box
              sx={{
                p: 4,
                borderRadius: "18px",
                background: "linear-gradient(135deg, #6C3BFF, #9C27B0)",
                color: "white",
              }}
            >
              <Typography variant="h6">Рекомендация</Typography>
              <Typography mt={2}>{result.short_recommendation}</Typography>
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
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
      borderBottom: (theme) => `1px solid ${theme.palette.divider}`,
    }}
  >
    <Typography color="text.secondary">{label}</Typography>
    <Typography color={green ? "success.main" : "text.primary"} fontWeight={600}>
      {value}
    </Typography>
  </Box>
);

export default CustomCheckResult;
