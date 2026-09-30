import React, { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../services/api";
import { Result } from "../types";
import { Award, CheckCircle, XCircle, Clock, ShieldCheck, ArrowLeft, FileText } from "lucide-react";

export const ResultsPage: React.FC = () => {
  const [results, setResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchParams] = useSearchParams();
  const highlightedId = searchParams.get("highlight");

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const data = await api.getMyResults();
        setResults(data);
      } catch (err: any) {
        setError(err.message || "Failed to load examination results.");
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-indigo-600 font-semibold text-xs uppercase tracking-wider mb-1">
            <Award className="w-4 h-4" />
            <span>Academic Performance Record</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">My Examination Results</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Tamper-proof academic grades evaluated and permanently sealed by the server
          </p>
        </div>

        <Link
          to="/student"
          className="inline-flex items-center space-x-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium px-4 py-2 rounded-xl text-xs transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Exams</span>
        </Link>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-16 text-slate-400">Loading verified grade records...</div>
      ) : results.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center max-w-lg mx-auto">
          <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-800">No Results Found</h3>
          <p className="text-sm text-slate-500 mt-1">
            You haven''t completed any examinations yet.
          </p>
          <Link
            to="/student"
            className="inline-block mt-4 bg-indigo-600 text-white font-medium px-4 py-2 rounded-xl text-xs hover:bg-indigo-700 transition"
          >
            Browse Available Examinations
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {results.map((res) => {
            const isHighlighted = highlightedId && parseInt(highlightedId, 10) === res.id;

            return (
              <div
                key={res.id}
                className={`bg-white rounded-2xl border p-6 shadow-sm transition-all ${
                  isHighlighted ? "border-indigo-500 ring-2 ring-indigo-200 bg-indigo-50/20" : "border-slate-200"
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-3">
                      <span className="text-xs font-mono font-semibold text-slate-400">
                        Result ID #{res.id}
                      </span>
                      <span className="text-xs text-slate-400 flex items-center space-x-1">
                        <Clock className="w-3.5 h-3.5" />
                        <span>{new Date(res.evaluated_at).toLocaleString()}</span>
                      </span>
                      <span className="inline-flex items-center space-x-1 text-[11px] bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full font-semibold border border-indigo-100">
                        <ShieldCheck className="w-3 h-3 text-indigo-600" />
                        <span>Sealed & Verified</span>
                      </span>
                    </div>

                    <h3 className="text-lg font-bold text-slate-900">
                      Exam Session #{res.exam_id} Attempt #{res.attempt_id}
                    </h3>
                  </div>

                  <div className="flex items-center space-x-6 sm:border-l sm:border-slate-100 sm:pl-6">
                    <div className="text-right">
                      <div className="text-2xl font-black text-slate-900">
                        {res.total_score} <span className="text-sm font-normal text-slate-400">/ {res.max_score}</span>
                      </div>
                      <div className="text-xs font-semibold text-indigo-600">
                        {res.percentage.toFixed(1)}% Marks
                      </div>
                    </div>

                    <div className="flex-shrink-0">
                      {res.passed ? (
                        <div className="flex items-center space-x-1.5 bg-emerald-100 text-emerald-800 px-3 py-1.5 rounded-xl font-bold text-xs border border-emerald-300">
                          <CheckCircle className="w-4 h-4 text-emerald-600" />
                          <span>PASSED</span>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-1.5 bg-rose-100 text-rose-800 px-3 py-1.5 rounded-xl font-bold text-xs border border-rose-300">
                          <XCircle className="w-4 h-4 text-rose-600" />
                          <span>FAILED</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
