"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { api } from "@/lib/api-client";
import type { Salesperson, SalespersonPerformance, Recording } from "@samaa/shared";
import { KPICard } from "@/components/kpi-card";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Mic, TrendingUp, Target, Award } from "lucide-react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from "recharts";

export default function SalespersonDashboardPage() {
  const params = useParams();
  const salespersonId = params.id as string;

  const { data: salesperson } = useQuery({
    queryKey: ["salesperson", salespersonId],
    queryFn: () => api.get<Salesperson>(`/salespeople/${salespersonId}`),
    enabled: !!salespersonId,
  });

  const { data: performance } = useQuery({
    queryKey: ["salesperson", salespersonId, "performance"],
    queryFn: () =>
      api.get<SalespersonPerformance>(`/salespeople/${salespersonId}/performance`),
    enabled: !!salespersonId,
  });

  const radarData = performance
    ? [
        { skill: "Greeting", score: performance.avg_greeting_score ?? 0 },
        { skill: "Discovery", score: performance.avg_discovery_score ?? 0 },
        { skill: "Product", score: performance.avg_product_knowledge_score ?? 0 },
        { skill: "Objection", score: performance.avg_objection_handling_score ?? 0 },
        { skill: "Closing", score: performance.avg_closing_score ?? 0 },
      ]
    : [];

  return (
    <div className="space-y-6 p-6">
      {/* Profile Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{salesperson?.name || "Salesperson"}</h1>
        <p className="text-muted-foreground">
          {salesperson?.role || "Sales Associate"}
          {salesperson?.shift ? ` · ${salesperson.shift}` : ""}
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Conversations"
          value={performance?.total_conversations ?? 0}
          icon={Mic}
          description="Total handled"
        />
        <KPICard
          title="Closing Rate"
          value={
            performance?.conversion_rate != null
              ? `${(performance.conversion_rate * 100).toFixed(0)}%`
              : "—"
          }
          icon={Target}
          description="Sales conversion"
        />
        <KPICard
          title="Avg Score"
          value={
            performance?.avg_overall_score != null
              ? performance.avg_overall_score.toFixed(1)
              : "—"
          }
          icon={Award}
          description="Overall performance"
        />
        <KPICard
          title="Trend"
          value="—"
          icon={TrendingUp}
          description="vs. last period"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Skill Radar Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Skill Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="skill" className="text-sm" />
                  <PolarRadiusAxis domain={[0, 100]} className="text-xs" />
                  <Radar
                    name="Score"
                    dataKey="score"
                    stroke="hsl(var(--primary))"
                    fill="hsl(var(--primary))"
                    fillOpacity={0.2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Coaching Recommendations */}
        <Card>
          <CardHeader>
            <CardTitle>Coaching Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              AI-powered coaching recommendations will appear here based on conversation analysis.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
