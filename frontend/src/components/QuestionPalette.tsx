import React from "react";

interface QuestionPaletteProps {
  totalQuestions: number;
  currentIndex: number;
  answeredIndices: Set<number>;
  markedIndices?: Set<number>;
  onSelectQuestion: (index: number) => void;
}

export const QuestionPalette: React.FC<QuestionPaletteProps> = ({
  totalQuestions,
  currentIndex,
  answeredIndices,
  markedIndices = new Set(),
  onSelectQuestion,
}) => {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
        <div>
          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Question Palette</h4>
          <span className="text-[11px] text-slate-500">Fast Navigation Grid</span>
        </div>
        <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
          {answeredIndices.size} / {totalQuestions} Answered
        </span>
      </div>

      <div className="grid grid-cols-5 gap-2 max-h-64 overflow-y-auto pr-1">
        {Array.from({ length: totalQuestions }, (_, i) => {
          const isCurrent = i === currentIndex;
          const isAnswered = answeredIndices.has(i);
          const isMarked = markedIndices.has(i);

          let buttonStyle = "bg-slate-100 text-slate-600 border border-slate-200 hover:bg-slate-200";

          if (isMarked) {
            buttonStyle = "bg-purple-100 text-purple-800 border border-purple-300 font-bold hover:bg-purple-200";
          } else if (isAnswered) {
            buttonStyle = "bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold hover:bg-emerald-200";
          }

          if (isCurrent) {
            buttonStyle += " ring-2 ring-indigo-600 ring-offset-2";
          }

          return (
            <button
              key={i}
              onClick={() => onSelectQuestion(i)}
              className={`h-9 w-9 rounded-xl font-semibold text-xs flex items-center justify-center transition-all ${buttonStyle}`}
            >
              {i + 1}
            </button>
          );
        })}
      </div>

      <div className="pt-3 border-t border-slate-100 grid grid-cols-3 gap-1 text-[11px] text-slate-600 font-medium">
        <div className="flex items-center space-x-1.5">
          <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
          <span>Answered</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <div className="w-3 h-3 rounded-full bg-purple-500"></div>
          <span>Review</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <div className="w-3 h-3 rounded-full bg-slate-300"></div>
          <span>Pending</span>
        </div>
      </div>
    </div>
  );
};
