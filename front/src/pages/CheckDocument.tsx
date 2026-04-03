// src/pages/CheckDocument.tsx
import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api"; 
import {
  Container,
  Stack,
  Paper,
  Typography,
  Button,
  RadioGroup,
  FormControlLabel,
  Radio,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  CircularProgress, 
  Backdrop,
} from "@mui/material";
import {
  UploadFile,
  CheckCircle,
  Warning,
  ErrorOutline,
  InfoOutlined,
} from "@mui/icons-material";
import { API_ROUTES, FILE_CONFIG, CHECK_TYPES } from "../config/constants";
import { Footer } from "components";

// Компонент окна загрузки
const AnalyzingOverlay: React.FC<{ open: boolean; filename?: string }> = ({ open, filename }) => (
  <Backdrop
    open={open}
    sx={{
      zIndex: 9999,
      flexDirection: "column",
      gap: 3,
      bgcolor: "rgba(0,0,0,0.85)",
      color: "white",
    }}
  >
    <CircularProgress size={80} thickness={4} sx={{ color: "primary.main" }} />
    <Typography variant="h5" fontWeight={700} textAlign="center">
      Анализируем документ...
    </Typography>
    {filename && (
      <Typography variant="body1" sx={{ opacity: 0.7 }} textAlign="center">
        {filename}
      </Typography>
    )}
    <Typography variant="body2" sx={{ opacity: 0.5 }} textAlign="center">
      Это может занять несколько секунд
    </Typography>
  </Backdrop>
);


const CheckDocumentPage: React.FC = () => {
  const navigate = useNavigate();

  const [selectedType, setSelectedType] = useState<keyof typeof CHECK_TYPES>("GOST");
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleTypeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedType(event.target.value as keyof typeof CHECK_TYPES);
  };

  const handleChooseFile = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files?.[0]) {
      setFile(event.target.files[0]);
    }
  };

  // Polling - ждем пока статус не станет финальным
  const pollUntilReady = async (checkId: string | number): Promise<void> => {
    const MAX_ATTEMPTS = 60;   // максимум 3 минуты
    const POLL_INTERVAL = 3000; // каждые 3 секунды

    for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
      try {
        const res = await api.get(API_ROUTES.DOCUMENTS.CHECK_RESULT(String(checkId)));
        const data = res.data;

        console.log(`Попытка ${attempt + 1}: статус =`, data?.status);

        const isProcessing =
          data?.status === "Анализируется" ||
          data?.status === "analyzing" ||
          (data?.total_checks === 0 && data?.passed_checks === 0 && !data?.errors?.length);

        if (!isProcessing) {
          console.log("Проверка завершена!");
          return;
        }
      } catch (err) {
        console.error("Ошибка polling:", err);
      }

      await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));
    }

    console.warn("Таймаут polling - переходим на страницу результата");
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Выберите файл!");
      return;
    }

    if (file.size > FILE_CONFIG.MAX_SIZE_BYTES) {
      alert(`Файл слишком большой. Максимальный размер: ${FILE_CONFIG.MAX_SIZE_MB} МБ`);
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      console.log("📤 Загружаю файл...");
      const uploadRes = await api.post(API_ROUTES.DOCUMENTS.UPLOAD, formData);
      const { document_id } = uploadRes.data;

      console.log("✅ Документ загружен, ID:", document_id);

      console.log("🔍 Запускаю проверку ГОСТ...");
      const checkRes = await api.post(API_ROUTES.DOCUMENTS.CHECK_START, {
        document_id,
      });

      console.log("📊 Ответ от /gost-check/start:", checkRes.data);

      const checkId = checkRes.data.check_id;

      if (!checkId) {
        console.error("❌ check_id не получен!", checkRes.data);
        alert("Ошибка: не получен ID проверки");
        return;
      }

      setUploading(false);
      setAnalyzing(true);

      // Polling пока проверка не завершится
      await pollUntilReady(checkId);

      // Переходим на результат только когда готово
      navigate(API_ROUTES.DOCUMENTS.CHECK_RESULT(checkId));

      console.log("✅ check_id получен:", checkId);
      console.log("🚀 Переход на:", API_ROUTES.DOCUMENTS.CHECK_RESULT(checkId));
    } catch (err: any) {
      console.error("❌ Ошибка:", err.response?.data);
      alert("Ошибка: " + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
      setAnalyzing(false);
    }
  };

  

  return (
    <>
       {/* Оверлей анализа */}
      <AnalyzingOverlay open={uploading || analyzing} filename={file?.name} />

      <Container maxWidth="lg" sx={{ py: 6 }}>
        <Stack direction={{ xs: "column", md: "row" }} spacing={4} alignItems="flex-start">
          <Stack flex={2} spacing={3}>
            <Paper
              variant="outlined"
              sx={{
                p: 4,
                textAlign: "center",
                borderStyle: "dashed",
                borderColor: dragging ? "primary.dark" : "primary.main",
                bgcolor: dragging ? "action.hover" : "inherit",
                transition: "background-color 0.2s, border-color 0.2s",
              }}
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                setDragging(false);
              }}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                const droppedFile = e.dataTransfer.files[0];
                if (
                  droppedFile &&
                  (droppedFile.type === "application/pdf" ||
                    droppedFile.name.match(/\.(doc|docx)$/))
                ) {
                  setFile(droppedFile);
                } else {
                  alert("Допустимы только PDF и DOCX файлы");
                }
              }}
            >
              <UploadFile sx={{ fontSize: 48, color: "primary.main", mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Перетащите PDF или DOCX
              </Typography>
              <Typography variant="body2" sx={{ color: "text.secondary", mb: 3 }}>
                или нажмите для выбора файла <br /> Максимальный размер: {FILE_CONFIG.MAX_SIZE_MB} МБ
              </Typography>

              <input
                ref={fileInputRef}
                type="file"
                accept={FILE_CONFIG.ALLOWED_TYPES.join(",")}
                style={{ display: "none" }}
                onChange={handleFileChange}
              />

              <Button variant="contained" color="primary" onClick={handleChooseFile}>
                Выбрать файл
              </Button>

              {file && (
                <Box sx={{ mt: 2, display: "flex", alignItems: "center", justifyContent: "center", gap: 2 }}>
                  <Typography variant="body1">
                    Выбран файл: <b>{file.name}</b>
                  </Typography>
                  <Button
                    variant="outlined"
                    color="error"
                    size="small"
                    onClick={() => setFile(null)}
                  >
                    Удалить
                  </Button>
                </Box>
              )}
            </Paper>

            <Paper variant="outlined" sx={{ p: 4 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>Тип проверки</Typography>
              <RadioGroup value={selectedType} onChange={handleTypeChange}>
                <FormControlLabel
                  value={CHECK_TYPES.GOST}
                  control={<Radio color="primary" />}
                  label="ГОСТ — проверка по государственным стандартам"
                />
                <FormControlLabel
                  value={CHECK_TYPES.INTERNAL}
                  control={<Radio color="primary" />}
                  label="Внутренний стандарт — корпоративные требования"
                />
                <FormControlLabel
                  value={CHECK_TYPES.CUSTOM}
                  control={<Radio color="primary" />}
                  label="Пользовательский шаблон — настраиваемые правила"
                />
              </RadioGroup>
            </Paper>

            <Box textAlign="center">
              <Button
                variant="contained"
                color="primary"
                size="large"
                disabled={uploading || !file}
                onClick={handleUpload}
                sx={{ borderRadius: "12px", px: 5, py: 1.5, fontWeight: 600 }}
              >
                {uploading || analyzing ? "Анализируем..." : "Начать проверку"}
              </Button>
            </Box>
          </Stack>

          <Stack flex={1} spacing={3}>
            <Paper sx={{ p: 3, borderRadius: "12px" }}>
              <Typography variant="h6" gutterBottom>Пример отчёта</Typography>
              <LinearProgress variant="determinate" value={85} sx={{ height: 10, borderRadius: 5, mb: 2 }} />
              <Typography sx={{ fontWeight: 600, textAlign: "right" }}>8.5/10</Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
                  <ListItemText primary="Структура — Отлично" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Warning color="warning" /></ListItemIcon>
                  <ListItemText primary="Оформление — Требует внимания" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
                  <ListItemText primary="Содержание — Соответствует" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><ErrorOutline color="error" /></ListItemIcon>
                  <ListItemText primary="Библиография — Ошибки" />
                </ListItem>
              </List>
            </Paper>

            <Paper sx={{ p: 3, borderRadius: "12px" }}>
              <Typography variant="h6" gutterBottom>Советы</Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><InfoOutlined color="primary" /></ListItemIcon>
                  <ListItemText primary="Убедитесь, что документ содержит все обязательные разделы" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><InfoOutlined color="primary" /></ListItemIcon>
                  <ListItemText primary="Проверьте правильность оформления списка литературы" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><InfoOutlined color="primary" /></ListItemIcon>
                  <ListItemText primary="Используйте единый стиль форматирования заголовков" />
                </ListItem>
              </List>
            </Paper>
          </Stack>
        </Stack>
      </Container>
    </>
  );
};

export default CheckDocumentPage;