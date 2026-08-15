"use client";

import { useState, useEffect, useCallback } from 'react';
import { backendApi } from '@/lib/backend-api';

export interface BackendStatus {
  isOnline: boolean;
  isChecking: boolean;
  lastChecked: Date | null;
  error: string | null;
}

export const useBackendStatus = (checkInterval: number = 30000) => {
  const [status, setStatus] = useState<BackendStatus>({
    isOnline: false,
    isChecking: true,
    lastChecked: null,
    error: null,
  });

  const checkStatus = useCallback(async () => {
    setStatus(prev => ({ ...prev, isChecking: true, error: null }));
    
    try {
      const isHealthy = await backendApi.healthCheck();
      setStatus({
        isOnline: isHealthy,
        isChecking: false,
        lastChecked: new Date(),
        error: null,
      });
    } catch (error) {
      setStatus({
        isOnline: false,
        isChecking: false,
        lastChecked: new Date(),
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }, []);

  useEffect(() => {
    // Initial check
    checkStatus();

    // Set up interval for periodic checks
    const interval = setInterval(checkStatus, checkInterval);

    return () => clearInterval(interval);
  }, [checkStatus, checkInterval]);

  return {
    ...status,
    checkStatus,
  };
};