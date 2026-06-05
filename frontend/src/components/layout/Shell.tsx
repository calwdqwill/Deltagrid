"use client";

import { ReactNode, Suspense } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

interface ShellProps {
  children: ReactNode;
}

export function Shell({ children }: ShellProps) {
  return (
    <div className="flex h-screen bg-[#070A12] text-slate-100">
      <Suspense fallback={<div className="h-screen w-64 border-r border-white/10 bg-[#070A12]" />}>
        <Sidebar />
      </Suspense>
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 overflow-auto bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,0.10),transparent_30%),linear-gradient(180deg,#0A0F1D_0%,#070A12_100%)] p-4 xl:p-5">
          {children}
        </main>
      </div>
    </div>
  );
}
