import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Shield, LogOut, User as UserIcon, BookOpen, Layers, ShieldAlert } from "lucide-react";

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const getRoleBadge = (role: string) => {
    switch (role) {
      case "ADMIN":
        return <span className="bg-purple-100 text-purple-700 text-xs px-2 py-0.5 rounded-full font-medium">Administrator</span>;
      case "FACULTY":
        return <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full font-medium">Faculty Examiner</span>;
      case "STUDENT":
        return <span className="bg-emerald-100 text-emerald-700 text-xs px-2 py-0.5 rounded-full font-medium">Student Candidate</span>;
      default:
        return null;
    }
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center space-x-3">
          <div className="bg-indigo-600 text-white p-2 rounded-lg shadow-sm">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight text-slate-900">Secure<span className="text-indigo-600">Exam</span></span>
            <span className="hidden sm:inline-block ml-2 text-xs bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded border border-slate-200 font-mono">v1.0-SSE</span>
          </div>
        </Link>

        {user ? (
          <div className="flex items-center space-x-6">
            <nav className="flex items-center space-x-4">
              {user.role === "STUDENT" && (
                <>
                  <Link to="/student" className="text-sm font-medium text-slate-600 hover:text-indigo-600 flex items-center space-x-1.5">
                    <BookOpen className="w-4 h-4" />
                    <span>My Exams</span>
                  </Link>
                  <Link to="/student/results" className="text-sm font-medium text-slate-600 hover:text-indigo-600">
                    My Results
                  </Link>
                </>
              )}

              {user.role === "FACULTY" && (
                <>
                  <Link to="/faculty" className="text-sm font-medium text-slate-600 hover:text-indigo-600 flex items-center space-x-1.5">
                    <Layers className="w-4 h-4" />
                    <span>Exam Studio</span>
                  </Link>
                </>
              )}

              {user.role === "ADMIN" && (
                <>
                  <Link to="/admin" className="text-sm font-medium text-slate-600 hover:text-indigo-600 flex items-center space-x-1.5">
                    <ShieldAlert className="w-4 h-4" />
                    <span>Governance</span>
                  </Link>
                </>
              )}
            </nav>

            <div className="flex items-center space-x-3 pl-4 border-l border-slate-200">
              <div className="flex flex-col items-end">
                <span className="text-sm font-semibold text-slate-800 flex items-center space-x-1">
                  <UserIcon className="w-3.5 h-3.5 text-slate-400" />
                  <span>{user.full_name}</span>
                </span>
                <div>{getRoleBadge(user.role)}</div>
              </div>
              <button
                onClick={handleLogout}
                title="Sign out securely"
                className="p-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-center space-x-3">
            <Link
              to="/login"
              className="text-sm font-medium text-slate-700 hover:text-indigo-600 px-3 py-1.5 rounded-lg hover:bg-slate-50 transition"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded-lg shadow-sm transition"
            >
              Register Candidate
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};
