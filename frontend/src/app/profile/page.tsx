"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Shell } from "@/components/layout/Shell";
import { useAuthStore } from "@/stores/authStore";
import { useLocale } from "@/hooks/useLocale";
import { User, Mail, Crown } from "lucide-react";

export default function ProfilePage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const { t } = useLocale();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, router]);

  return (
    <Shell>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-primary-text mb-6">{t.nav.profile}</h1>

        <div className="bg-white rounded-lg border border-border p-6 space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-accent-blue flex items-center justify-center text-white text-2xl font-bold">
              {(user?.username || user?.email || "U")[0].toUpperCase()}
            </div>
            <div>
              <div className="text-lg font-semibold text-primary-text">
                {user?.username || user?.email || "Anonymous"}
              </div>
              <div className="flex items-center gap-1 text-sm text-secondary-text">
                <Crown className="w-4 h-4" />
                <span className="capitalize">{user?.plan || "free"}</span>
              </div>
            </div>
          </div>

          <div className="border-t border-border pt-4 space-y-3">
            <div className="flex items-center gap-3 text-sm">
              <Mail className="w-4 h-4 text-secondary-text" />
              <span className="text-secondary-text">Email:</span>
              <span className="text-primary-text">{user?.email || "—"}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <User className="w-4 h-4 text-secondary-text" />
              <span className="text-secondary-text">User ID:</span>
              <span className="text-primary-text font-mono text-xs">{user?.id || "—"}</span>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}
