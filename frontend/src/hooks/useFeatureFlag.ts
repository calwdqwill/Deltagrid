"use client";

import { useAuthStore } from "@/stores/authStore";

/**
 * Check if the current user has a feature flag enabled.
 * Returns false for anonymous users or if the flag is not set.
 *
 * Phase 6: Feature flag foundation. Used for plan-based gating
 * and gradual feature rollouts.
 */
export function useFeatureFlag(key: string): boolean {
  const hasFeature = useAuthStore((state) => state.hasFeature);
  return hasFeature(key);
}
