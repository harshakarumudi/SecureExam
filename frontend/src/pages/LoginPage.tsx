import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Shield, Lock, Mail, AlertCircle, ArrowRight } from "lucide-react";

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const user = await login(email, password);
      if (user.role === "STUDENT") {
        navigate("/student");
      } else if (user.role === "FACULTY") {
        navigate("/faculty");
      } else if (user.role === "ADMIN") {
        navigate("/admin");
      } else {
        navigate("/");
      }
    } catch (err: any) {
      setError(err.message || "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickFill = (accEmail: string, accPass: string) => {
    setEmail(accEmail);
    setPassword(accPass);
    setError(null);
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center p-3 bg-indigo-50 text-indigo-600 rounded-xl mb-2">
            <Shield className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Portal Authentication</h2>
          <p className="text-xs text-slate-500">Sign in to access your secure examination workstation</p>
        </div>

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 text-sm p-3.5 rounded-xl flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-500" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Institutional Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@secureexam.edu"
                className="w-full pl-10 pr-3 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Account Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-3 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium py-2.5 rounded-xl shadow-sm transition flex items-center justify-center space-x-2 text-sm"
          >
            <span>{loading ? "Authenticating..." : "Sign In"}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Evaluator Quick-Fill Buttons */}
        <div className="pt-4 border-t border-slate-100">
          <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2 text-center">
            Evaluator Quick Fill
          </div>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => handleQuickFill("student@secureexam.edu", "StudentPass123!@#")}
              className="text-[11px] bg-slate-100 hover:bg-slate-200 text-slate-700 py-1.5 px-2 rounded-lg font-medium transition"
            >
              Student Demo
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill("faculty@secureexam.edu", "FacultyPass123!@#")}
              className="text-[11px] bg-slate-100 hover:bg-slate-200 text-slate-700 py-1.5 px-2 rounded-lg font-medium transition"
            >
              Faculty Demo
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill("admin@secureexam.edu", "AdminPass123!@#")}
              className="text-[11px] bg-slate-100 hover:bg-slate-200 text-slate-700 py-1.5 px-2 rounded-lg font-medium transition"
            >
              Admin Demo
            </button>
          </div>
        </div>

        <div className="text-center text-xs text-slate-500 pt-2">
          New examinee?{" "}
          <Link to="/register" className="text-indigo-600 hover:text-indigo-800 font-semibold">
            Register Candidate Account
          </Link>
        </div>
      </div>
    </div>
  );
};
