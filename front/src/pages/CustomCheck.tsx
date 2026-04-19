import React, { useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Container,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { UploadFile } from "@mui/icons-material";

import { api } from "../api";
import { API_ROUTES, ROUTES } from "../config/constants";

type SemanticResponse = {
  document_id: number;
  filename?: string;
  ruleset_code: string;
  overall_score?: number;
  score_label?: string;
  status?: string;
  summary?: Record<string, unknown>;
  findings?: Array<Record<string, unknown>>;
  short_recommendation?: string;
};

const CustomCheck: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const documentId = useMemo(() => {
    const raw = searchParams.get("document_id");
    const parsed = raw ? Number(raw) : NaN;
    return Number.isFinite(parsed) ? parsed : null;
  }, [searchParams]);

  const [gostFile, setGostFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rulesetCode, setRulesetCode] = useState<string | null>(null);

  if (!documentId) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Alert severity="warning" sx={{ mb: 3 }}>
          Не найден `document_id`. Сначала загрузите проверяемый документ на странице проверки.
        </Alert>
        <Button variant="contained" onClick={() => navigate(ROUTES.CHECK)}>
          Вернуться к загрузке документа
        </Button>
      </Container>
    );
  }

  const runCustomCheck = async () => {
    if (!gostFile) {
      setError("Выберите PDF с ГОСТ для извлечения правил.");
      return;
    }

    if (!gostFile.name.toLowerCase().endsWith(".pdf")) {
      setError("Для извлечения правил поддерживается только PDF.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const extractPayload = new FormData();
      extractPayload.append("file", gostFile);

      const extractRes = await api.post(API_ROUTES.DOCUMENTS.RULE_EXTRACT, extractPayload);
      const code = extractRes.data?.ruleset_code;
      if (!code) {
        throw new Error("Сервис не вернул ruleset_code.");
      }
      setRulesetCode(code);

      const semanticRes = await api.post(
        API_ROUTES.DOCUMENTS.SEMANTIC_CHECK(documentId, code),
      );

      navigate(ROUTES.CHECK_RESULT(String(documentId)), {
        state: {
          resultType: "semantic",
          semanticResult: semanticRes.data as SemanticResponse,
        },
      });
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Ошибка при запуске кастомной проверки.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Stack spacing={3}>
        <Typography variant="h4" fontWeight={700}>
          Кастомная проверка документа
        </Typography>
        <Typography color="text.secondary">
          Документ уже загружен. Теперь загрузите PDF с вашим ГОСТ, чтобы извлечь правила и запустить проверку.
        </Typography>

        <Paper variant="outlined" sx={{ p: 4, textAlign: "center", borderStyle: "dashed" }}>
          <UploadFile sx={{ fontSize: 48, color: "primary.main", mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Загрузите PDF с ГОСТ
          </Typography>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            style={{ display: "none" }}
            onChange={(event) => {
              if (event.target.files?.[0]) {
                setGostFile(event.target.files[0]);
              }
            }}
          />
          <Button variant="contained" onClick={() => fileInputRef.current?.click()}>
            Выбрать PDF
          </Button>

          {gostFile && (
            <Box sx={{ mt: 2 }}>
              <Typography>Выбран файл: <b>{gostFile.name}</b></Typography>
            </Box>
          )}
        </Paper>

        {rulesetCode && (
          <Alert severity="info">Сгенерирован ruleset: {rulesetCode}</Alert>
        )}
        {error && <Alert severity="error">{error}</Alert>}

        <Box>
          <Button
            variant="contained"
            size="large"
            onClick={runCustomCheck}
            disabled={loading || !gostFile}
          >
            {loading ? (
              <>
                <CircularProgress size={18} sx={{ mr: 1 }} />
                Обрабатываем...
              </>
            ) : (
              "Извлечь правила и запустить проверку"
            )}
          </Button>
        </Box>
      </Stack>
    </Container>
  );
};

export default CustomCheck;
