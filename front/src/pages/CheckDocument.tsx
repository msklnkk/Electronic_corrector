// src/pages/CheckDocument.tsx
import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom"; 
import api from '../api/axios.config';
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
} from "@mui/material";
import {
  UploadFile,
  CheckCircle,
  Warning,
  ErrorOutline,
  InfoOutlined,
} from "@mui/icons-material";

const CheckDocumentPage: React.FC = () => {
  const navigate = useNavigate();

  // Состояние для выбора типа проверки
  const [selectedType, setSelectedType] = useState("gost");

  // новое состояние для подсветки при перетаскивании
  const [dragging, setDragging] = useState(false);

  // выбранный файл
  const [file, setFile] = useState<File | null>(null);

  // статус загрузки
  const [uploading, setUploading] = useState(false);

  // ref для скрытого input
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleTypeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedType(event.target.value);
  };

  // клик по кнопке открывает диалог
  const handleChooseFile = () => {
    fileInputRef.current?.click();
  };

  // пользователь выбрал файл
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files?.[0]) {
      setFile(event.target.files[0]);
    }
  };

  const handleUpload = async () => {
  if (!file) {
    alert("Выберите файл!");
    return;
  }

  setUploading(true);

  try {
    const formData = new FormData();
    formData.append("file", file);

    const uploadRes = await api.post("/upload", formData);
    const { document_id } = uploadRes.data;

    console.log("Документ загружен, ID:", document_id);

    // ПРАВИЛЬНЫЙ ПУТЬ!
    const checkRes = await api.post("/gost-check/start", {
      document_id: document_id
    });

    const checkId = checkRes.data.check_id;  

    alert("Проверка ГОСТ запущена!");
    navigate(`/check-result/${checkId}`);  

  } catch (err: any) {
    console.error("Ошибка:", err.response?.data);
    alert("Ошибка: " + (err.response?.data?.detail || err.message));
  } finally {
    setUploading(false);
  }
};
  return (
    <>
      <Container maxWidth="lg" sx={{ py: 6 }}>
        <Stack direction={{ xs: "column", md: "row" }} spacing={4} alignItems="flex-start">
          {/* Левая часть — полностью твоё оформление */}
          <Stack flex={2} spacing={3}>
            <Paper 
              variant="outlined" 
              sx={{ 
                p: 4, 
                textAlign: "center", 
                borderStyle: "dashed", 
                borderColor: dragging ? "primary.dark" : "primary.main",
                bgcolor: dragging ? "action.hover" : "inherit",
                transition: "background-color 0.2s, border-color 0.2s" 
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
                  if (droppedFile && (droppedFile.type === "application/pdf" || droppedFile.name.match(/\.(doc|docx)$/))) {
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
                или нажмите для выбора файла <br /> Максимальный размер: 50 МБ
              </Typography>
              
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.doc,.docx"
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

            {/* ТИП ПРОВЕРКИ — РАБОЧИЙ */}
            <Paper variant="outlined" sx={{ p: 4 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>Тип проверки</Typography>
              <RadioGroup value={selectedType} onChange={handleTypeChange}>
                <FormControlLabel
                  value="gost"
                  control={<Radio color="primary" />}
                  label="ГОСТ — проверка по государственным стандартам"
                />
                <FormControlLabel
                  value="internal"
                  control={<Radio color="primary" />}
                  label="Внутренний стандарт — корпоративные требования"
                />
                <FormControlLabel
                  value="custom"
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
                disabled={uploading}
                onClick={handleUpload}
                sx={{ borderRadius: "12px", px: 5, py: 1.5, fontWeight: 600 }}
              >
                {uploading ? "Проверка запущена..." : "Начать проверку"}
              </Button>
            </Box>
          </Stack>

          {/* Правая часть — полностью твоя */}
          <Stack flex={1} spacing={3}>
            <Paper sx={{ p: 3, borderRadius: "12px" }}>
              <Typography variant="h6" gutterBottom>Пример отчёта</Typography>
              <LinearProgress variant="determinate" value={85} sx={{ height: 10, borderRadius: 5, mb: 2 }} />
              <Typography sx={{ fontWeight: 600, textAlign: "right" }}>8.5/10</Typography>
              <List dense>
                <ListItem><ListItemIcon><CheckCircle color="success" /></ListItemIcon><ListItemText primary="Структура — Отлично" /></ListItem>
                <ListItem><ListItemIcon><Warning color="warning" /></ListItemIcon><ListItemText primary="Оформление — Требует внимания" /></ListItem>
                <ListItem><ListItemIcon><CheckCircle color="success" /></ListItemIcon><ListItemText primary="Содержание — Соответствует" /></ListItem>
                <ListItem><ListItemIcon><ErrorOutline color="error" /></ListItemIcon><ListItemText primary="Библиография — Ошибки" /></ListItem>
              </List>
            </Paper>

            <Paper sx={{ p: 3, borderRadius: "12px" }}>
              <Typography variant="h6" gutterBottom>Советы</Typography>
              <List dense>
                <ListItem><ListItemIcon><InfoOutlined color="primary" /></ListItemIcon><ListItemText primary="Убедитесь, что документ содержит все обязательные разделы" /></ListItem>
                <ListItem><ListItemIcon><InfoOutlined color="primary" /></ListItemIcon><ListItemText primary="Проверьте правильность оформления списка литературы" /></ListItem>
                <ListItem><ListItemIcon><InfoOutlined color="primary" /></ListItemIcon><ListItemText primary="Используйте единый стиль форматирования заголовков" /></ListItem>
              </List>
            </Paper>
          </Stack>
        </Stack>
      </Container>

      <Box sx={{ textAlign: "center", py: 3, borderTop: 1, borderColor: "divider" }}>
        <Typography variant="body2" color="text.secondary">
          © 2025 Электронный корректор. Все права защищены.
        </Typography>
      </Box>
    </>
  );
};

export default CheckDocumentPage;