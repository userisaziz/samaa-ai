"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Inbox } from "lucide-react";
import type { FunnelStage } from "@samaa/shared";

interface SalesFunnelProps {
  data: FunnelStage[];
  title?: string;
  onStageClick?: (stage: string) => void;
}

const STAGE_COLORS = ["#3b82f6", "#f59e0b", "#22c55e"];

export function SalesFunnel({ data, title = "Sales Funnel", onStageClick }: SalesFunnelProps) {
  const hasData = data.length > 0 && data.some((d) => d.count > 0);
  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <Card className="shadow-[0_1px_3px_rgba(0,0,0,0.04),0_1px_2px_rgba(0,0,0,0.06)]">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-steel">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {hasData ? (
          <div className="flex flex-col items-center gap-2 py-4">
            {data.map((stage, i) => {
              const widthPercent = Math.max((stage.count / maxCount) * 100, 20);
              const prevCount = i > 0 ? data[i - 1].count : stage.count;
              const dropRate = prevCount > 0 ? ((1 - stage.count / prevCount) * 100).toFixed(0) : "0";

              return (
                <div key={stage.stage} className="w-full">
                  {i > 0 && (
                    <div className="flex items-center justify-center py-1">
                      <span className="text-xs text-steel font-mono">
                        {stage.count > 0 && prevCount > stage.count ? `-${dropRate}% drop` : ""}
                      </span>
                    </div>
                  )}
                  <div
                    className="flex items-center justify-center cursor-pointer transition-all hover:opacity-80"
                    style={{ width: `${widthPercent}%`, margin: "0 auto" }}
                    onClick={() => onStageClick?.(stage.stage)}
                  >
                    <div
                      className="w-full rounded-lg py-4 text-center"
                      style={{ backgroundColor: STAGE_COLORS[i] ?? "#94a3b8" }}
                    >
                      <p className="text-sm font-medium text-white">{stage.stage}</p>
                      <p className="text-lg font-bold text-white font-mono">{stage.count}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="flex h-[200px] flex-col items-center justify-center text-center">
            <Inbox className="h-8 w-8 text-stone/40 mb-2" />
            <p className="text-sm text-steel">No funnel data yet</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
