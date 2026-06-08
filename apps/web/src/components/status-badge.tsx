"use client";

import { Badge } from "@/components/ui/badge";
import type { RecordingStatus } from "@samaa/shared";

const statusConfig: Record<RecordingStatus, { label: string; className: string }> = {
  UPLOADED: { label: "Uploaded", className: "bg-yellow-100 text-yellow-800 border-yellow-200" },
  PREPROCESSING: { label: "Preprocessing", className: "bg-blue-100 text-blue-800 border-blue-200" },
  TRANSCRIBING: { label: "Transcribing", className: "bg-blue-100 text-blue-800 border-blue-200" },
  DIARIZING: { label: "Diarizing", className: "bg-blue-100 text-blue-800 border-blue-200" },
  SEGMENTING: { label: "Segmenting", className: "bg-blue-100 text-blue-800 border-blue-200" },
  ANALYZING: { label: "Analyzing", className: "bg-blue-100 text-blue-800 border-blue-200" },
  SCORING: { label: "Scoring", className: "bg-blue-100 text-blue-800 border-blue-200" },
  COMPLETED: { label: "Completed", className: "bg-green-100 text-green-800 border-green-200" },
  FAILED: { label: "Failed", className: "bg-red-100 text-red-800 border-red-200" },
};

export function StatusBadge({ status }: { status: RecordingStatus }) {
  const config = statusConfig[status] || {
    label: status,
    className: "bg-gray-100 text-gray-800 border-gray-200",
  };

  return (
    <Badge variant="outline" className={config.className}>
      {config.label}
    </Badge>
  );
}
