"use client";

import { useEffect, useMemo, useRef } from "react";
import type { TranscriptSegment, Conversation } from "@samaa/shared";
import { cn } from "@/lib/utils";

/** Role-based color palette — salesperson gets brand green, customer gets blue. */
const ROLE_COLORS: Record<string, string> = {
  salesperson: "text-brand-green-deep",
  customer: "text-blue-600",
};

/** Fallback speaker colors when no role classification is available. */
const SPEAKER_COLORS: Record<string, string> = {
  SPEAKER_00: "text-blue-600",
  SPEAKER_01: "text-brand-green-deep",
  SPEAKER_02: "text-purple-600",
  SPEAKER_03: "text-amber-600",
  UNKNOWN: "text-stone",
};

/** Confidence threshold below which we show a visual indicator. */
const LOW_CONFIDENCE_THRESHOLD = 0.7;

function getRoleDisplayLabel(
  seg: TranscriptSegment,
  salespersonName?: string,
): string {
  if (!seg.role_label) {
    // Fallback: show raw speaker label
    return seg.speaker_label.replace("SPEAKER_", "S");
  }
  const role = seg.role_label.toLowerCase();
  if (role === "salesperson" && salespersonName) return salespersonName;
  if (role === "salesperson") return "Salesperson";
  if (role === "customer") return "Customer";
  // Capitalize first letter for any other role
  return seg.role_label.charAt(0).toUpperCase() + seg.role_label.slice(1).toLowerCase();
}

function getRoleColor(seg: TranscriptSegment): string {
  if (!seg.role_label) {
    return SPEAKER_COLORS[seg.speaker_label] || "text-stone";
  }
  return ROLE_COLORS[seg.role_label.toLowerCase()] || "text-stone";
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

interface TranscriptViewerProps {
  segments: TranscriptSegment[];
  conversations?: Conversation[];
  activeConversationId?: string | null;
  currentTime?: number;
  salespersonName?: string;
  onSegmentClick?: (segment: TranscriptSegment) => void;
  onConversationHighlight?: (conversationId: string) => void;
}

export function TranscriptViewer({
  segments,
  conversations,
  activeConversationId,
  currentTime,
  salespersonName,
  onSegmentClick,
}: TranscriptViewerProps) {
  // Group segments by conversation time ranges
  const segmentsWithConversation = useMemo(() => {
    if (!conversations?.length) return segments.map((s) => ({ ...s, conversationId: null }));
    return segments.map((seg) => {
      const conv = conversations.find(
        (c) => seg.start_time >= c.start_time && seg.end_time <= c.end_time,
      );
      return { ...seg, conversationId: conv?.id ?? null };
    });
  }, [segments, conversations]);

  const activeSegmentRef = useRef<HTMLDivElement>(null);

  // Auto-scroll active segment into view
  useEffect(() => {
    if (activeSegmentRef.current) {
      activeSegmentRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, [currentTime]);

  if (segments.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-steel">
        No transcript available
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {segmentsWithConversation.map((seg) => {
        const isActiveConversation = activeConversationId && seg.conversationId === activeConversationId;
        const isActiveTime =
          currentTime !== undefined &&
          currentTime >= seg.start_time &&
          currentTime < seg.end_time;
        const isActive = isActiveConversation || isActiveTime;
        const isLowConfidence =
          seg.role_confidence != null && seg.role_confidence < LOW_CONFIDENCE_THRESHOLD;
        const displayLabel = getRoleDisplayLabel(seg, salespersonName);
        const labelColor = getRoleColor(seg);

        return (
          <div
            key={seg.id}
            ref={isActiveTime ? activeSegmentRef : undefined}
            className={cn(
              "flex gap-3 rounded-md px-3 py-2 text-sm transition-colors hover:bg-accent/50 cursor-pointer",
              isActiveConversation && "bg-accent",
              isActiveTime && !isActiveConversation && "bg-brand-green-soft/60",
            )}
            onClick={() => onSegmentClick?.(seg)}
          >
            <span className="shrink-0 font-mono text-xs text-steel pt-0.5">
              {formatTime(seg.start_time)}
            </span>
            <span
              className={cn(
                "shrink-0 w-24 text-xs font-semibold pt-0.5 flex items-center gap-1",
                labelColor,
              )}
              title={
                seg.role_label
                  ? `${seg.role_label} (${seg.speaker_label})${seg.role_confidence != null ? ` — ${Math.round(seg.role_confidence * 100)}% confidence` : ""}`
                  : seg.speaker_label
              }
            >
              <span className="truncate">{displayLabel}</span>
              {isLowConfidence && (
                <span
                  className="shrink-0 inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-amber-100 text-amber-700 text-[9px] font-bold"
                  title={`Low confidence: ${Math.round((seg.role_confidence ?? 0) * 100)}%`}
                >
                  ?
                </span>
              )}
            </span>
            <span className="flex-1">{seg.text}</span>
          </div>
        );
      })}
    </div>
  );
}
