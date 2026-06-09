"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { RecordingStatus } from "@samaa/shared";

const PROCESSING_STATES: RecordingStatus[] = [
  "PREPROCESSING",
  "TRANSCRIBING",
  "DIARIZING",
  "SEGMENTING",
  "ANALYZING",
  "SCORING",
];

const statusConfig: Record<RecordingStatus, { label: string; className: string; dot?: string }> = {
  UPLOADED: { label: "Uploaded", className: "bg-stone/10 text-slate border-stone/20" },
  PREPROCESSING: { label: "Preprocessing", className: "bg-brand-tag/10 text-brand-tag border-brand-tag/20", dot: "bg-brand-tag" },
  TRANSCRIBING: { label: "Transcribing", className: "bg-brand-tag/10 text-brand-tag border-brand-tag/20", dot: "bg-brand-tag" },
  DIARIZING: { label: "Diarizing", className: "bg-brand-tag/10 text-brand-tag border-brand-tag/20", dot: "bg-brand-tag" },
  SEGMENTING: { label: "Segmenting", className: "bg-brand-tag/10 text-brand-tag border-brand-tag/20", dot: "bg-brand-tag" },
  ANALYZING: { label: "Analyzing", className: "bg-brand-tag/10 text-brand-tag border-brand-tag/20", dot: "bg-brand-tag" },
  SCORING: { label: "Scoring", className: "bg-brand-tag/10 text-brand-tag border-brand-tag/20", dot: "bg-brand-tag" },
  COMPLETED: { label: "Completed", className: "bg-brand-green-soft text-brand-green-deep border-brand-green/30", dot: "bg-brand-green-deep" },
  FAILED: { label: "Failed", className: "bg-destructive/10 text-destructive border-destructive/20", dot: "bg-destructive" },
};

export function StatusBadge({ status }: { status: RecordingStatus }) {
  const config = statusConfig[status] || {
    label: status,
    className: "bg-gray-100 text-gray-800 border-gray-200",
  };

  const isProcessing = PROCESSING_STATES.includes(status);

  return (
    <Badge variant="outline" className={cn("gap-1.5 text-[12px] font-medium", config.className)}>
      {config.dot && (
        <span
          className={cn(
            "h-1.5 w-1.5 rounded-full shrink-0",
            config.dot,
            isProcessing && "animate-pulse",
          )}
        />
      )}
      {config.label}
    </Badge>
  );
}
