import React, { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Container,
  Divider,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
  InputAdornment,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import { api } from "../api";
import { API_ROUTES, ROUTES } from "../config/constants";

const FONT_OPTIONS = [
  "Times New Roman",
  "Arial",
  "Calibri",
  "Courier New",
  "Georgia",
];

const SECTION_OPTIONS: { value: string; label: string }[] = [
  { value: "введение", label: "Введение" },
  { value: "заключение", label: "Заключение" },
  { value: "содержание", label: "Содержание" },
  { value: "список источников", label: "Список источников" },
  { value: "приложение", label: "Приложение" },
  { value: "аннотация", label: "Аннотация" },
];

const UserTemplateCheck: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const documentId = useMemo(() => {
    const raw = searchParams.get("document_id");
    const parsed = raw ? Number(raw) : NaN;
    return Number.isFinite(parsed) ? parsed : null;
  }, [searchParams]);

  const [fontName, setFontName] = useState<string>("");
  const [fontSize, setFontSize] = useState<string>("");
  const [paragraphIndent, setParagraphIndent] = useState<string>("");
  const [marginLeft, setMarginLeft] = useState<string>("");
  const [marginRight, setMarginRight] = useState<string>("");
  const [marginTop, setMarginTop] = useState<string>("");
  const [marginBottom, setMarginBottom] = useState<string>("");
  const [sections, setSections] = useState<string[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!documentId) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Alert severity="warning" sx={{ mb: 3 }}>
          Не найден document_id. Сначала загрузите проверяемый документ.
        </Alert>
        <Button variant="contained" onClick={() => navigate(ROUTES.CHECK)}>
          Вернуться к загрузке
        </Button>
      </Container>
    );
  }

  const toggleSection = (value: string) => {
    setSections((prev) =>
      prev.includes(value) ? prev.filter((s) => s !== value) : [...prev, value]
    );
  };

  const numOrNull = (s: string) => {
    const n = parseFloat(s);
    return Number.isFinite(n) ? n : null;
  };

  const handleSubmit = async () => {
    const body: Record<string, unknown> = {};

    if (fontName) body.font_name = fontName;
    if (fontSize) body.font_size = numOrNull(fontSize);
    if (paragraphIndent) body.paragraph_indent_cm = numOrNull(paragraphIndent);
    if (marginLeft) body.margin_left_mm = numOrNull(marginLeft);
    if (marginRight) body.margin_right_mm = numOrNull(marginRight);
    if (marginTop) body.margin_top_mm = numOrNull(marginTop);
    if (marginBottom) body.margin_bottom_mm = numOrNull(marginBottom);
    if (sections.length > 0) body.required_sections = sections;

    const hasAnyRule = Object.values(body).some((v) => v !== null && v !== undefined);
    if (!hasAnyRule) {
      setError("Укажите хотя бы одно правило для проверки.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const startTime = Date.now();
      const res = await api.post(
        API_ROUTES.DOCUMENTS.USER_TEMPLATE_CHECK(documentId),
        body
      );
      const elapsedMs = Date.now() - startTime;

      const historyKey = `user_template_${documentId}_${Date.now()}`;
      const stateToSave = { result: res.data, elapsedMs };

      try {
        localStorage.setItem(`userTemplateResult_${historyKey}`, JSON.stringify(stateToSave));
        const histRaw = localStorage.getItem("userTemplateCheckHistory");
        const hist: unknown[] = histRaw ? JSON.parse(histRaw) : [];
        hist.unshift({
          check_id: historyKey,
          document_id: documentId,
          checked_at: new Date().toISOString(),
          score: res.data.score,
          type: "user_template",
          filename: res.data.filename,
        });
        localStorage.setItem("userTemplateCheckHistory", JSON.stringify(hist.slice(0, 20)));
      } catch { /* ignore */ }

      navigate(ROUTES.USER_TEMPLATE_CHECK_RESULT, {
        state: stateToSave,
      });
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Ошибка при запуске проверки."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Typography
        sx={{ cursor: "pointer", opacity: 0.6, mb: 2, "&:hover": { opacity: 1 } }}
        onClick={() => navigate(-1)}
      >
        ← Вернуться назад
      </Typography>

      <Typography variant="h4" fontWeight={700} mb={1}>
        Пользовательский шаблон
      </Typography>
      <Typography color="text.secondary" mb={4}>
        Выберите параметры документа вручную. Будут проверены только те правила,
        для которых вы задали значения.
      </Typography>

      <Stack spacing={4}>
        {/* Шрифт */}
        <Box>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Шрифт
          </Typography>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <FormControl size="small" sx={{ minWidth: 220 }}>
              <FormLabel sx={{ mb: 0.5 }}>Название шрифта</FormLabel>
              <Select
                value={fontName}
                onChange={(e) => setFontName(e.target.value)}
                displayEmpty
              >
                <MenuItem value="">
                  <em>Не проверять</em>
                </MenuItem>
                {FONT_OPTIONS.map((f) => (
                  <MenuItem key={f} value={f}>
                    {f}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Box>
              <FormLabel sx={{ display: "block", mb: 0.5 }}>Размер</FormLabel>
              <TextField
                size="small"
                type="number"
                placeholder="14"
                value={fontSize}
                onChange={(e) => setFontSize(e.target.value)}
                InputProps={{ endAdornment: <InputAdornment position="end">пт</InputAdornment> }}
                sx={{ width: 120 }}
              />
            </Box>
          </Stack>
        </Box>

        <Divider />

        {/* Поля страницы */}
        <Box>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Поля страницы
          </Typography>
          <Stack direction="row" spacing={2} flexWrap="wrap">
            {[
              { label: "Левое", value: marginLeft, setter: setMarginLeft },
              { label: "Правое", value: marginRight, setter: setMarginRight },
              { label: "Верхнее", value: marginTop, setter: setMarginTop },
              { label: "Нижнее", value: marginBottom, setter: setMarginBottom },
            ].map(({ label, value, setter }) => (
              <Box key={label}>
                <FormLabel sx={{ display: "block", mb: 0.5 }}>{label}</FormLabel>
                <TextField
                  size="small"
                  type="number"
                  placeholder="20"
                  value={value}
                  onChange={(e) => setter(e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">мм</InputAdornment> }}
                  sx={{ width: 110 }}
                />
              </Box>
            ))}
          </Stack>
        </Box>

        <Divider />

        {/* Абзацный отступ */}
        <Box>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Абзацный отступ
          </Typography>
          <Box>
            <FormLabel sx={{ display: "block", mb: 0.5 }}>Отступ</FormLabel>
            <TextField
              size="small"
              type="number"
              placeholder="1.25"
              value={paragraphIndent}
              onChange={(e) => setParagraphIndent(e.target.value)}
              InputProps={{ endAdornment: <InputAdornment position="end">см</InputAdornment> }}
              sx={{ width: 140 }}
            />
          </Box>
        </Box>

        <Divider />

        {/* Обязательные разделы */}
        <Box>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Обязательные разделы
          </Typography>
          <FormGroup row>
            {SECTION_OPTIONS.map(({ value, label }) => (
              <FormControlLabel
                key={value}
                control={
                  <Checkbox
                    checked={sections.includes(value)}
                    onChange={() => toggleSection(value)}
                    size="small"
                  />
                }
                label={label}
                sx={{ minWidth: 180 }}
              />
            ))}
          </FormGroup>
        </Box>

        {error && <Alert severity="error">{error}</Alert>}

        <Box>
          <Button
            variant="contained"
            size="large"
            onClick={handleSubmit}
            disabled={loading}
            sx={{ px: 5 }}
          >
            {loading ? (
              <>
                <CircularProgress size={18} sx={{ mr: 1 }} />
                Проверяем...
              </>
            ) : (
              "Запустить проверку"
            )}
          </Button>
        </Box>
      </Stack>
    </Container>
  );
};

export default UserTemplateCheck;
