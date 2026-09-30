import React from "react";
import { Link } from "react-router-dom";
import { Shield, Clock, Lock, FileCheck2, Cpu } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export const LandingPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-16 py-12">
      {/* Hero Section */}
      <section className="text-center max-w-4xl mx-auto px-4 space-y-6">
        <div className="inline-flex items-center space-x-2 bg-indigo-50 border border-indigo-200 text-indigo-700 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider">
          <Shield className="w-3.5 h-3.5" />
          <span>Amrita School of Computing — Academic SSE Project</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight">
          Secure Online Examination <br />
          <span className="text-indigo-600">Management System</span>
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
          Engineered with uncompromising defense-in-depth principles: server-authoritative countdown timers,
          tamper-proof evaluation engines, Argon2id credential hashing, and zero-trust object authorization.
        </p>

        <div className="flex items-center justify-center space-x-4 pt-4">
          {user ? (
            <Link
              to={user.role === "STUDENT" ? "/student" : user.role === "FACULTY" ? "/faculty" : "/admin"}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-6 py-3 rounded-xl shadow-md transition"
            >
              Go to Your Dashboard ({user.role})
            </Link>
          ) : (
            <>
              <Link
                to="/login"
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-6 py-3 rounded-xl shadow-md transition"
              >
                Sign In to Portal
              </Link>
              <Link
                to="/register"
                className="bg-white hover:bg-slate-50 text-slate-700 font-medium px-6 py-3 rounded-xl border border-slate-300 shadow-sm transition"
              >
                Candidate Registration
              </Link>
            </>
          )}
        </div>
      </section>

      {/* Security Architecture Pillars */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl font-bold text-slate-900">Security-by-Design Architecture</h2>
          <p className="text-slate-500 text-sm mt-1">Directly satisfying CO1, CO2, CO3, and CO4 course outcomes</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition">
            <div className="bg-indigo-50 text-indigo-600 p-3 rounded-xl w-fit mb-4">
              <Clock className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Authoritative Server Timer</h3>
            <p className="text-slate-600 text-sm leading-relaxed">
              Browser clocks and local storage are treated as untrusted. Submissions are strictly verified against the
              server''s cryptographic deadline timestamp (`expires_at`), hard-rejecting late submissions.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition">
            <div className="bg-indigo-50 text-indigo-600 p-3 rounded-xl w-fit mb-4">
              <Lock className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">BOLA & IDOR Mitigation</h3>
            <p className="text-slate-600 text-sm leading-relaxed">
              Every request enforces object-level resource ownership on the backend. Students cannot access peers'' scores,
              and faculty cannot tamper with exams they do not own.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition">
            <div className="bg-indigo-50 text-indigo-600 p-3 rounded-xl w-fit mb-4">
              <FileCheck2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Tamper-Proof Evaluation</h3>
            <p className="text-slate-600 text-sm leading-relaxed">
              Clients never transmit scores, correct flags, or mark calculations. The server evaluation engine queries
              canonical database keys and seals the result record permanently.
            </p>
          </div>
        </div>
      </section>

      {/* Demo Credentials Guide */}
      <section className="max-w-4xl mx-auto px-4">
        <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white p-8 rounded-2xl shadow-xl">
          <div className="flex items-center space-x-3 mb-4">
            <Cpu className="w-6 h-6 text-indigo-400" />
            <h3 className="text-xl font-bold">Evaluator Test Accounts</h3>
          </div>
          <p className="text-slate-300 text-sm mb-6">
            The platform is pre-seeded with verified test accounts across all three RBAC roles for immediate testing:
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
            <div className="bg-white/10 p-3.5 rounded-xl border border-white/10">
              <div className="font-bold text-emerald-400 mb-1 text-sm">Student Account</div>
              <div className="text-slate-200">student@secureexam.edu</div>
              <div className="text-slate-400">StudentPass123!@#</div>
            </div>

            <div className="bg-white/10 p-3.5 rounded-xl border border-white/10">
              <div className="font-bold text-blue-400 mb-1 text-sm">Faculty Account</div>
              <div className="text-slate-200">faculty@secureexam.edu</div>
              <div className="text-slate-400">FacultyPass123!@#</div>
            </div>

            <div className="bg-white/10 p-3.5 rounded-xl border border-white/10">
              <div className="font-bold text-purple-400 mb-1 text-sm">Admin Account</div>
              <div className="text-slate-200">admin@secureexam.edu</div>
              <div className="text-slate-400">AdminPass123!@#</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

