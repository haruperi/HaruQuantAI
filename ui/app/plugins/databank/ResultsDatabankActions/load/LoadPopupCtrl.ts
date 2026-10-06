import { useState, useEffect } from 'react';
import { subscribeMockLoadProgress } from './LoadService';

export function useLoadPopup(onFinished: () => void): number {
  const [progress, setProgress] = useState(0);

  useEffect(() => subscribeMockLoadProgress(setProgress), []);

  useEffect(() => {
    if (progress >= 100) {
      const t = setTimeout(onFinished, 350);
      return () => clearTimeout(t);
    }
  }, [progress, onFinished]);

  return progress;
}
