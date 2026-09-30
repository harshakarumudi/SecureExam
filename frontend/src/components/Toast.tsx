import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, X } from "lucide-react";

export type ToastType = "success" | "error" | "warning";

interface ToastProps {
  message: string;
  type: ToastType;
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({ message, type, onClose }) => {
  const getIcon = () => {
    switch (type) {
      case "success":
        return <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
      case "error":
        return <XCircle className="w-5 h-5 text-rose-500" />;
      case "warning":
        return <AlertTriangle className="w-5 h-5 text-amber-500" />;
    }
  };

  const getBorder = () => {
    switch (type) {
      case "success":
        return "border-emerald-200 bg-emerald-50/90 text-emerald-900";
      case "error":
        return "border-rose-200 bg-rose-50/90 text-rose-900";
      case "warning":
        return "border-amber-200 bg-amber-50/90 text-amber-900";
    }
  };

  return (
    <div className={`fixed bottom-6 right-6 z-50 flex items-center space-x-3 p-4 rounded-xl border shadow-lg backdrop-blur-sm max-w-md ${getBorder()}`}>
      <div className="flex-shrink-0">{getIcon()}</div>
      <div className="text-sm font-medium flex-1">{message}</div>
      <button onClick={onClose} className="p-1 rounded-md hover:bg-black/5 transition">
        <X className="w-4 h-4 opacity-70" />
      </button>
    </div>
  );
};
