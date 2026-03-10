import { useState, useEffect, useCallback } from 'react';
import { getTokenUsage } from '@/services/api';
import type { TokenUsageResponse } from '@/services/api';

export function useTokenUsage() {
  const [usage, setUsage] = useState<TokenUsageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetch_ = useCallback(() => {
    setLoading(true);
    setError(null);
    getTokenUsage()
      .then(setUsage)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err : new Error('Failed to load usage'));
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetch_();
  }, [fetch_]);

  return { usage, loading, error, refetch: fetch_ };
}
