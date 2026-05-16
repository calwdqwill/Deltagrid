"use client";

import { useState } from "react";
import { useAuthStore } from "@/stores/authStore";
import { useLocale } from "@/hooks/useLocale";
import { useOrderIntents, useOrders, useCancelOrderIntent } from "@/hooks/useExecution";
import { useExchangeAccounts } from "@/hooks/useExchangeAccounts";
import { useExecutionSessions, useStartExecutionSession, useStopExecutionSession } from "@/hooks/useExecutionSessions";
import OrderIntentModal from "@/components/execution/OrderIntentModal";
import { Shell } from "@/components/layout/Shell";
import { Plus, XCircle, ShieldAlert, CheckCircle, Clock, AlertTriangle, Play, Square } from "lucide-react";

const STATUS_ICONS: Record<string, React.ReactNode> = {
  intent: <Clock size={14} className="text-blue-500" />,
  riskChecked: <ShieldAlert size={14} className="text-amber-500" />,
  pendingConfirmation: <AlertTriangle size={14} className="text-amber-500" />,
  submitted: <CheckCircle size={14} className="text-purple-500" />,
  filled: <CheckCircle size={14} className="text-green-500" />,
  partiallyFilled: <CheckCircle size={14} className="text-teal-500" />,
  cancelled: <XCircle size={14} className="text-slate-400" />,
  rejected: <XCircle size={14} className="text-red-500" />,
  failed: <XCircle size={14} className="text-red-500" />,
};

export default function ExecutionPage() {
  const { t } = useLocale();
  const { isAuthenticated } = useAuthStore();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"intents" | "orders">("intents");

  const { data: intents, isLoading: intentsLoading } = useOrderIntents({ enabled: isAuthenticated });
  const { data: orders, isLoading: ordersLoading } = useOrders({ enabled: isAuthenticated });
  const { data: sessions } = useExecutionSessions({ enabled: isAuthenticated });
  const startSession = useStartExecutionSession();
  const stopSession = useStopExecutionSession();
  const cancelIntent = useCancelOrderIntent();

  if (!isAuthenticated) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-slate-500">Please sign in to view execution dashboard.</p>
      </div>
    );
  }

  const items = activeTab === "intents" ? intents || [] : orders || [];
  const isLoading = activeTab === "intents" ? intentsLoading : ordersLoading;

  return (
    <Shell>
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{t.execution.title}</h1>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus size={16} />
          {t.execution.newIntent}
        </button>
      </div>

      <div className="mb-4 flex items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab("intents")}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              activeTab === "intents" ? "bg-blue-600 text-white" : "bg-white text-slate-600 border border-slate-200"
            }`}
          >
            {t.execution.intents}
          </button>
          <button
            onClick={() => setActiveTab("orders")}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              activeTab === "orders" ? "bg-blue-600 text-white" : "bg-white text-slate-600 border border-slate-200"
            }`}
          >
            {t.execution.orders}
          </button>
        </div>
        <div className="flex items-center gap-2">
          {sessions && sessions.length > 0 && sessions[0].status === "running" ? (
            <button
              onClick={() => stopSession.mutate(sessions[0].id)}
              className="flex items-center gap-1 rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-100"
            >
              <Square size={14} />
              Stop Session
            </button>
          ) : (
            <button
              onClick={() => startSession.mutate({ name: "Manual", isLive: false })}
              className="flex items-center gap-1 rounded-lg border border-green-200 bg-green-50 px-3 py-1.5 text-sm font-medium text-green-600 hover:bg-green-100"
            >
              <Play size={14} />
              Start Session
            </button>
          )}
        </div>
      </div>

      {isLoading && <p className="text-slate-500">Loading...</p>}

      {!isLoading && items.length === 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center">
          <p className="text-slate-500">No {activeTab} yet.</p>
        </div>
      )}

      <div className="space-y-3">
        {items.map((item: any) => (
          <div
            key={item.id}
            className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4"
          >
            <div className="flex items-center gap-3">
              {STATUS_ICONS[item.status] || <Clock size={14} className="text-slate-400" />}
              <div>
                <div className="text-sm font-semibold text-slate-900">
                  {item.symbol} <span className="text-slate-400">·</span> {item.side?.toUpperCase()}
                </div>
                <div className="text-xs text-slate-500">
                  {item.orderType} · Qty: {item.quantity} · Status: {item.status}
                </div>
              </div>
            </div>
            {activeTab === "intents" && (
              <button
                onClick={() => cancelIntent.mutate(item.id)}
                className="rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
              >
                <XCircle size={16} />
              </button>
            )}
          </div>
        ))}
      </div>

      <OrderIntentModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </div>
    </Shell>
  );
}
