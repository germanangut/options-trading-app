import { useEffect, useState } from "react";

export function useElapsedTimer(startedAt: number | null | undefined, active: boolean) {
  const [elapsedMs, setElapsedMs] = useState(0);

  useEffect(() => {
    if (!active || !startedAt) {
      setElapsedMs(0);
      return undefined;
    }

    const updateElapsed = () => {
      setElapsedMs(Math.max(0, Date.now() - startedAt));
    };

    updateElapsed();
    const intervalId = window.setInterval(updateElapsed, 1000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [active, startedAt]);

  return elapsedMs;
}