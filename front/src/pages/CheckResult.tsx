// src/pages/CheckResult.tsx
import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/axios.config";
import { Box, Typography, CircularProgress } from "@mui/material";

const Card = ({ children }: any) => (
  <Box
    sx={{
      background: "rgba(25,28,40,0.9)",
      borderRadius: "18px",
      p: 4,
      backdropFilter: "blur(12px)",
      border: "1px solid rgba(255,255,255,0.05)",
      boxShadow: "0 0 40px rgba(0,0,0,0.6)",
    }}
  >
    {children}
  </Box>
);

const GradientButton = ({ children, color }: any) => (
  <Box
    sx={{
      px: 5,
      py: 1.6,
      borderRadius: "12px",
      fontWeight: 600,
      cursor: "pointer",
      textAlign: "center",
      background:
        color === "purple"
          ? "linear-gradient(90deg,#7B5CFF,#9C27B0)"
          : "linear-gradient(90deg,#00E5FF,#00BCD4)",
      color: "#fff",
      transition: "0.3s",
      "&:hover": { transform: "translateY(-2px)", opacity: 0.9 },
    }}
  >
    {children}
  </Box>
);

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

  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchResult = useCallback(async () => {
    try {
      const res = await api.get(`/gost-check/result/${id}`);
      setResult(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (!id) return;
    fetchResult();
  }, [id, fetchResult]);

  if (loading)
    return (
      <Box sx={{ textAlign: "center", py: 10, color: "#fff" }}>
        <CircularProgress />
      </Box>
    );

  if (!result) return null;

const cleanFilename = (name?: string) => {
  if (!name) return "Документ";

  // убираем "1770331941_09bb1dea_" в начале
  const cleaned = name.replace(/^\d+_[a-f0-9]+_/, "");

  return cleaned || "Документ";
};

const documentName = cleanFilename(result.filename);

const rawScore = result.score ?? 0;
  const score =
    typeof rawScore === "string"
      ? Number(rawScore.replace(/^0+/, "")) || 0
      : Number(rawScore);

  const normalizedScore = Math.min(Math.max(score, 0), 10);
    const percent = Math.round((normalizedScore / 10) * 100);

  const statusText = normalizedScore >= 8 ? "Хорошо" : "Требует внимания";

  // ---- errors/warnings from backend ----
  const backendErrors: string[] = Array.isArray(result.errors)
    ? result.errors
    : [];
  const backendWarnings: string[] = Array.isArray(result.warnings)
    ? result.warnings
    : [];

  const criticalCount = backendErrors.length;
  const warningCount = backendWarnings.length;

  // ---- map strings -> table rows ----
  const mappedErrors: IssueRow[] = backendErrors.map((text) => ({
    type: "Ошибка",
    category: "ГОСТ",
    description: text,
    page: "-",
    priority: "Критично",
  }));

  const mappedWarnings: IssueRow[] = backendWarnings.map((text) => ({
    type: "Замечание",
    category: "ГОСТ",
    description: text,
    page: "-",
    priority: "Средний",
  }));

  const issues: IssueRow[] = [...mappedErrors, ...mappedWarnings];


  const analysisTime =
    result.analysis_time ||
    (typeof result.analysis_time_ms === "number"
      ? `${(result.analysis_time_ms / 1000).toFixed(1)} сек`
      : "-");

  const pagesChecked = result.pages_checked || "-";
  const accuracy = result.accuracy || "-";

  const recommendation =
    result.recommendation ||
    (normalizedScore >= 8
      ? "Документ оформлен хорошо. Можно сдавать."
      : normalizedScore >= 5
      ? "Есть важные замечания. Лучше исправить перед сдачей."
      : "Документ сильно не соответствует ГОСТ. Требуется доработка.");


  const errors = result.errors || [];

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at top left,#1B1F2F,#0E1018 60%)",
        color: "#fff",
        px: 8,
        py: 6,
      }}
    >
      {/* Назад */}
      <Typography
        sx={{ cursor: "pointer", opacity: 0.6, mb: 2 }}
        onClick={() => navigate(-1)}
      >
        ← Вернуться назад
      </Typography>

      <Typography variant="h4" fontWeight={700} mb={4}>
        Результаты проверки • {documentName}
      </Typography>

      <Box sx={{ display: "flex", gap: 4 }}>
        {/* LEFT */}
        <Box sx={{ flex: 3, display: "flex", flexDirection: "column", gap: 4 }}>
          {/* Score */}
          <Card>
            <Typography variant="h6" mb={3}>
              Общая оценка
            </Typography>

            <Box sx={{ display: "flex", alignItems: "center", gap: 6 }}>
              <Box sx={{ position: "relative" }}>
                <CircularProgress
                  variant="determinate"
                  value={(normalizedScore / 10) * 100}
                  size={160}
                  thickness={6}
                  sx={{
                    color: "#8A5CFF",
                    "& .MuiCircularProgress-circle": {
                      strokeLinecap: "round",
                    },
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
                <Typography color="gray" mt={1}>
                  {result.status || "Результат проверки"}
                </Typography>

                <Box sx={{ display: "flex", gap: 2, mt: 3 }}>
                  <Box sx={badgeStyle("#2ecc71")}>{statusText}</Box>
                  <Box sx={badgeStyle("#e74c3c")}>
                    {criticalCount} критичных
                  </Box>
                  <Box sx={badgeStyle("#f1c40f")}>
                    {warningCount} замечаний
                  </Box>
                </Box>
              </Box>
            </Box>
          </Card>

          {/* Errors */}
          <Card>
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
                      color:
                        e.priority === "Критично" ? "#ff7675" : "#f1c40f",
                      fontWeight: 600,
                    }}
                  >
                    {e.priority}
                  </span>
                </Box>
              ))
            )}
          </Card>

          <Box sx={{ display: "flex", gap: 3 }}>
            <GradientButton color="purple">
              Скачать отчет в PDF
            </GradientButton>
            <GradientButton color="cyan">
              Исправить документ
            </GradientButton>
          </Box>
        </Box>

        {/* RIGHT */}
        <Box sx={{ flex: 1, display: "flex", flexDirection: "column", gap: 4 }}>
          <Card>
            <Typography variant="h6" mb={2}>
              ИИ анализ завершен
            </Typography>

            <InfoRow label="Время анализа" value={analysisTime} />
            <InfoRow label="Страниц проверено" value={pagesChecked} />
            <InfoRow label="Точность анализа" value={`${accuracy}%`} green />
          </Card>

          <Box
            sx={{
              p: 4,
              borderRadius: "18px",
              background:
                "linear-gradient(135deg,#6C3BFF,#9C27B0)",
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

const badgeStyle = (color: string) => ({
  background: `${color}22`,
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
  borderBottom: "1px solid rgba(255,255,255,0.08)",
};

const tableRow = {
  display: "grid",
  gridTemplateColumns: "80px 160px 1fr 100px 120px",
  padding: "14px 0",
  borderBottom: "1px solid rgba(255,255,255,0.05)",
};

const InfoRow = ({ label, value, green }: any) => (
  <Box
    sx={{
      display: "flex",
      justifyContent: "space-between",
      py: 1.5,
      borderBottom: "1px solid rgba(255,255,255,0.05)",
    }}
  >
    <Typography color="gray">{label}</Typography>
    <Typography color={green ? "#2ecc71" : "#fff"} fontWeight={600}>
      {value}
    </Typography>
  </Box>
);

export default CheckResult;
