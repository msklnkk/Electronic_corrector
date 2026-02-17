//src/components/common/Footer.tsx
import React from "react";
import {
  Box,
  Container,
  Stack,
  Typography,
  Link,
  Divider,
} from "@mui/material";
import { Email, Phone, Telegram } from "@mui/icons-material";

const Footer: React.FC = () => {
  return (
    <Box
      component="footer"
      sx={{
        py: 6,
        bgcolor: "background.paper",
        borderTop: 1,
        borderColor: "divider",
      }}
    >
      <Container maxWidth="lg">
        <Stack
          direction={{ xs: "column", md: "row" }}
          spacing={4}
          justifyContent="space-between"
          alignItems="flex-start"
        >
          <Box sx={{ maxWidth: 300 }}>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
              <Box
                component="img"
                src="/logo.png"
                alt="Логотип"
                sx={{ height: 40, width: "auto" }}
              />
              <Typography variant="h6" fontWeight={700}>
                Электронный корректор
              </Typography>
            </Stack>
            <Typography variant="body2" color="text.secondary">
              Автоматизированная проверка документов на соответствие ГОСТ и корпоративным
              стандартам
            </Typography>
          </Box>

          <Box>
            <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 2 }}>
              Контакты
            </Typography>
            <Stack spacing={1}>
              <Link
                href="mailto:support@corrector.ru"
                color="text.secondary"
                underline="hover"
                sx={{ display: "flex", alignItems: "center", gap: 1 }}
              >
                <Email fontSize="small" /> support@corrector.ru
              </Link>
              <Link
                href="tel:+74951234567"
                color="text.secondary"
                underline="hover"
                sx={{ display: "flex", alignItems: "center", gap: 1 }}
              >
                <Phone fontSize="small" /> +7 (495) 123-45-67
              </Link>
              <Link
                href="https://t.me/electronic_corrector"
                target="_blank"
                rel="noopener"
                color="primary"
                underline="hover"
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                  fontWeight: 500,
                  mt: 1,
                }}
              >
                <Telegram fontSize="small" />
                Подписаться в Telegram
              </Link>
            </Stack>
          </Box>
        </Stack>

        <Divider sx={{ my: 4 }} />

        <Typography variant="body2" color="text.secondary" align="center">
          © 2025 Электронный корректор. Все права защищены.
        </Typography>
      </Container>
    </Box>
  );
};

export default Footer;