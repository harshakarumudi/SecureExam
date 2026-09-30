import React, { useState, useEffect } from "react";
import { Clock } from "lucide-react";

interface TimerDisplayProps {
  expiresAt: string;
  onExpire: () => void;
}

export const TimerDisplay: React.FC<TimerDisplayProps> = ({ expiresAt, onExpire }) => {
  const [secondsRemaining, setSecondsRemaining] = useState<number>(() => {
    const diff = Math.floor((new Date(expiresAt).getTime() - new Date().getTime()) / 1000);
    return Math.max(0, diff);
  });

  useEffect(() => {
    const interval = setInterval(() => {
      const diff = Math.floor((new Date(expiresAt).getTime() - new Date().getTime()) / 1000);
      if (diff <= 0) {
        setSecondsRemaining(0);
        clearInterval(interval);
        onExpire();
      } else {
        setSecondsRemaining(diff);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [expiresAt, onExpire]);

  const minutes = Math.floor(secondsRemaining / 60);
  const seconds = secondsRemaining % 60;
  const formatted = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;

  const isLowTime = secondsRemaining <= 300;
  const isCritical = secondsRemaining <= 60;

  return (
    <div
      className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border font-mono font-bold text-sm tracking-wide transition-all ${
        isCritical
          ? "bg-rose-50 text-rose-700 border-rose-300 animate-pulse"
          : isLowTime
          ? "bg-amber-50 text-amber-700 border-amber-300"
          : "bg-slate-50 text-slate-700 border-slate-200"
      }`}
    >
      <Clock className={`w-4 h-4 ${isCritical ? "text-rose-600" : isLowTime ? "text-amber-600" : "text-slate-500"}`} />
      <span>{formatted}</span>
    </div>
  );
};
