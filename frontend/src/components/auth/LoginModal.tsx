"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { useLocale } from "@/hooks/useLocale";
import { login, register } from "@/lib/api";
import { cn } from "@/lib/utils";
import { MessageCircle, Wallet } from "lucide-react";

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const { t } = useLocale();
  const { login: loginStore } = useAuthStore();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = isRegister
        ? await register({ email, password, username: username || undefined })
        : await login({ email, password });
      const data = res.data;
      loginStore(
        {
          id: data.user.id,
          email: data.user.email,
          username: data.user.username,
          plan: data.user.plan,
        },
        data.accessToken,
        data.refreshToken
      );
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="fixed inset-0 bg-black/60 z-50" onClick={onClose} />
      <div className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border border-white/10 bg-[#0D1322] p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-slate-100">
            {isRegister ? t.auth.registerTitle : t.auth.loginTitle}
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/[0.06] text-slate-500 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 px-4 py-3 rounded-lg border border-rose-400/20 bg-rose-500/10 text-rose-200 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1.5">
                {t.auth.username}
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-white/10 bg-black/20 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1.5">
              {t.auth.email}
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-white/10 bg-black/20 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1.5">
              {t.auth.password}
            </label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-white/10 bg-black/20 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={cn(
              "w-full py-2.5 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 transition-colors",
              loading && "opacity-70 cursor-not-allowed"
            )}
          >
            {loading
              ? "..."
              : isRegister
              ? t.auth.registerButton
              : t.auth.loginButton}
          </button>
        </form>

        <div className="mt-4 text-center text-sm text-slate-500">
          {isRegister ? (
            <button
              onClick={() => setIsRegister(false)}
              className="text-indigo-300 hover:underline"
            >
              {t.auth.hasAccount}
            </button>
          ) : (
            <button
              onClick={() => setIsRegister(true)}
              className="text-indigo-300 hover:underline"
            >
              {t.auth.noAccount}
            </button>
          )}
        </div>

        <div className="mt-4 flex items-center gap-2">
          <div className="h-px flex-1 bg-white/10" />
          <span className="text-xs text-slate-500">or</span>
          <div className="h-px flex-1 bg-white/10" />
        </div>

        <div className="mt-3 grid grid-cols-2 gap-2">
          <button
            type="button"
            disabled
            className="inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-white/10 text-sm text-slate-500 hover:bg-white/[0.04] transition-colors opacity-60 cursor-not-allowed"
          >
            <MessageCircle className="w-4 h-4" />
            Telegram
          </button>
          <button
            type="button"
            disabled
            className="inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-white/10 text-sm text-slate-500 hover:bg-white/[0.04] transition-colors opacity-60 cursor-not-allowed"
          >
            <Wallet className="w-4 h-4" />
            Web3
          </button>
        </div>
      </div>
    </>
  );
}
