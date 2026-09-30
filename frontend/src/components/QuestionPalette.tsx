import React from "react";
import { CheckCircle2, Circle } from "lucide-react";

interface QuestionPaletteProps {
  totalQuestions: number;
  currentIndex: number;
  answeredIndices: Set<number>;
  onSelectQuestion: (index: number) => void;
}

export const QuestionPalette: React.FC<QuestionPaletteProps> = ({
  totalQuestions,
  currentIndex,
  answeredIndices,
  onSelectQuestion,
}) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">
        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Question Matrix</h4>
        <span className="text-xs font-medium text-slate-500">
          {answeredIndices.size} / {totalQuestions} answered
        </span>
      </div>

      <div className="grid grid-cols-5 gap-2 max-h-60 overflow-y-auto pr-1">
        {Array.from({ length: totalQuestions }, (_, i) => {
          const isCurrent = i === currentIndex;
          const isAnswered = answeredIndices.has(i);

          return (
            <button
              key={i}
              onClick={() => onSelectQuestion(i)}
              className={`h-9 w-9 rounded-lg font-bold text-xs flex items-center justify-center transition-all ${
                isCurrent
                  ? "bg-indigo-600 text-white ring-2 ring-indigo-400 ring-offset-1"
                  : isAnswered
                  ? "bg-emerald-100 text-emerald-800 border border-emerald-300 hover:bg-emerald-200"
                  : "bg-slate-100 text-slate-600 border border-slate-200 hover:bg-slate-200"
              }`}
            >
              {i + 1}
            </button>
          );
        })}
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
        <div className="flex items-center space-x-1">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
          <span>Answered</span>
        </div>
        <div className="flex items-center space-x-1">
          <Circle className="w-3.5 h-3.5 text-slate-400" />
          <span>Pending</span>
        </div>
      </div>
    </div>
  );
};
