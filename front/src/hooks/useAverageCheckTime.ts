// src/hooks/useAverageCheckTime.ts
import { useState, useEffect } from 'react';
// import { api } from '../api';
// import { API_ROUTES } from '../config/constants';

export const useAverageCheckTime = (userId?: number) => {
  const [averageTime, setAverageTime] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [totalChecks, setTotalChecks] = useState(0);

  useEffect(() => {
    const calculateFromLocalStorage = () => {
      try {
        const storageKey = 'checkAnalysisTimes';
        const raw = localStorage.getItem(storageKey);

        if (!raw) {
          setAverageTime(null);
          setTotalChecks(0);
          setLoading(false);
          return;
        }

        const parsed = JSON.parse(raw) as Record<string, number>;
        const values = Object.values(parsed)
          .map((v) => Number(v))
          .filter((v) => Number.isFinite(v) && v > 0);

        if (values.length === 0) {
          setAverageTime(null);
          setTotalChecks(0);
          setLoading(false);
          return;
        }

        const sum = values.reduce((acc, v) => acc + v, 0);
        const avg = sum / values.length;

        setAverageTime(avg);
        setTotalChecks(values.length);
      } catch (err) {
        console.error('Ошибка чтения среднего времени из localStorage:', err);
        setAverageTime(null);
        setTotalChecks(0);
      } finally {
        setLoading(false);
      }
    };

    // Пока userId нам не нужен, но оставим в зависимостях,
    // чтобы пересчитывать при смене пользователя
    calculateFromLocalStorage();
  }, [userId]);

  const formatTime = (seconds: number | null): string => {
    if (seconds === null) return '-';

    // Если меньше секунды - показываем миллисекунды
    if (seconds < 1) {
      return `${Math.round(seconds * 1000)} мс`;
    }

    // Если меньше минуты - показываем секунды
    if (seconds < 60) {
      return `${Math.round(seconds)} сек`;
    } 
    
    // Если меньше часа - показываем минуты
    if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const secs = Math.round(seconds % 60);
      return secs > 0 ? `${minutes} мин ${secs} сек` : `${minutes} мин`;
    } 
    
    // Если больше часа - показываем часы и минуты
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours} ч ${minutes} мин`;
  };

  return {
    averageTime,
    averageTimeFormatted: formatTime(averageTime),
    totalChecks,
    loading,
  };
};