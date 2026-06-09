"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import type { Store, Salesperson, SalespersonPerformance } from "@samaa/shared";
import { KPICard } from "@/components/kpi-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { Users, Mic, TrendingUp, AlertTriangle, Inbox } from "lucide-react";
import type { AnalyticsOverviewResponse, AnalyticsSalespeopleResponse } from "@samaa/shared";
import { OutcomeDonut } from "@/components/charts/outcome-donut";
import { ConversionGauge } from "@/components/charts/conversion-gauge";
import { ScoreTrend } from "@/components/charts/score-trend";
import { VolumeTrend } from "@/components/charts/volume-trend";
import { PerformanceBar } from "@/components/charts/performance-bar";
import { SkillRadarCompare } from "@/components/charts/skill-radar-compare";
import { ObjectionTreemap } from "@/components/charts/objection-treemap";
import { SkillHeatmap } from "@/components/charts/skill-heatmap";
import { SalesFunnel } from "@/components/charts/sales-funnel";

export default function StoreDashboardPage() {
  const params = useParams();
  const storeId = params.id as string;

  const { data: store } = useQuery({
    queryKey: ["store", storeId],
    queryFn: () => api.get<Store>(`/stores/${storeId}`),
    enabled: !!storeId,
  });

  const { data: salespeople } = useQuery({
    queryKey: ["salespeople", "store", storeId],
    queryFn: () => api.get<Salesperson[]>(`/salespeople?store_id=${storeId}`),
    enabled: !!storeId,
  });

  // Fetch performance for each salesperson
  const performanceQueries = useQuery({
    queryKey: ["store-performances", storeId, salespeople?.map((s) => s.id)],
    queryFn: async () => {
      if (!salespeople?.length) return new Map<string, SalespersonPerformance>();
      const results = await Promise.all(
        salespeople.map(async (sp) => {
          try {
            const perf = await api.get<SalespersonPerformance>(
              `/salespeople/${sp.id}/performance`,
            );
            return [sp.id, perf] as const;
          } catch {
            return [sp.id, null] as const;
          }
        }),
      );
      return new Map(
        results.filter(([, p]) => p !== null) as Iterable<[string, SalespersonPerformance]>,
      );
    },
    enabled: !!salespeople?.length,
  });

  const performances = performanceQueries.data ?? new Map<string, SalespersonPerformance>();

  // Compute store-level aggregates
  const perfValues = Array.from(performances.values());
  const avgStoreScore =
    perfValues.length > 0
      ? perfValues.reduce((sum, p) => sum + (p.avg_overall_score ?? 0), 0) / perfValues.length
      : null;
  const totalConversations = perfValues.reduce((sum, p) => sum + p.total_conversations, 0);

  // Find top objection from all salespeople (placeholder until aggregated endpoint exists)
  const topObjection = "—";

  // Fetch analytics overview + salespeople comparison
  const { data: analytics } = useQuery({
    queryKey: ["analytics-overview", "store", storeId],
    queryFn: () =>
      api.get<AnalyticsOverviewResponse>(`/analytics/overview?store_id=${storeId}`),
    enabled: !!storeId,
  });
  const { data: salespeopleComparison } = useQuery({
    queryKey: ["analytics-salespeople", "store", storeId],
    queryFn: () =>
      api.get<AnalyticsSalespeopleResponse>(`/analytics/salespeople-comparison?store_id=${storeId}`),
    enabled: !!storeId,
  });

  return (
    <div className="space-y-6 lg:space-y-8 p-4 sm:p-6 lg:p-8">
      {/* Breadcrumbs */}
      <Breadcrumbs
        items={[
          { label: store?.name || "Store" },
        ]}
      />

      {/* Store Header */}
      <div className="border-b border-border pb-4 sm:pb-6">
        <h1 className="text-[22px] sm:text-[28px] font-semibold tracking-tight text-ink leading-tight">{store?.name || "Store"}</h1>
        <p className="mt-1 text-sm text-steel">{store?.location || ""}</p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Performance Score"
          value={avgStoreScore != null ? avgStoreScore.toFixed(1) : "—"}
          icon={TrendingUp}
          description="Average across salespeople"
        />
        <KPICard
          title="Conversations"
          value={totalConversations}
          icon={Mic}
          description="Total analyzed"
        />
        <KPICard
          title="Salespeople"
          value={salespeople?.length ?? 0}
          icon={Users}
          description="Active in this store"
        />
        <KPICard
          title="Top Objection"
          value={topObjection}
          icon={AlertTriangle}
          description="Most common"
        />
      </div>

      {/* Analytics Charts */}
      {(analytics || salespeopleComparison) && (
        <>
          {/* Row 1: Outcome Donut + Conversion Gauge + Sales Funnel */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <OutcomeDonut data={analytics?.outcome_distribution ?? []} />
            <ConversionGauge
              value={analytics?.conversion_rate ?? null}
              label={`${analytics?.total_conversations ?? 0} conversations`}
            />
            <SalesFunnel data={analytics?.funnel_stages ?? []} />
          </div>

          {/* Row 2: Score Trend + Volume Trend */}
          <div className="grid gap-4 lg:grid-cols-2">
            <ScoreTrend data={analytics?.score_trend ?? []} />
            <VolumeTrend data={analytics?.volume_trend ?? []} />
          </div>

          {/* Row 3: Sales Performance Bar (within-store ranking) */}
          <PerformanceBar data={salespeopleComparison?.salespeople ?? []} />

          {/* Row 4: Skill Radar Comparison + Top Objections Treemap */}
          <div className="grid gap-4 lg:grid-cols-2">
            <SkillRadarCompare data={salespeopleComparison?.salespeople ?? []} />
            <ObjectionTreemap data={analytics?.top_objections ?? []} />
          </div>

          {/* Row 5: Team Skill Heatmap */}
          {salespeopleComparison?.salespeople && salespeopleComparison.salespeople.length > 0 && (
            <SkillHeatmap data={salespeopleComparison.salespeople} />
          )}
        </>
      )}

      {/* Salesperson Performance Table */}
      <Card className="shadow-[0_1px_3px_rgba(0,0,0,0.04),0_1px_2px_rgba(0,0,0,0.06)]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-4 w-4 text-steel" />
            Salesperson Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          {salespeople && salespeople.length > 0 ? (
            <div className="overflow-x-auto -mx-6 sm:mx-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-wider text-steel">Name</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-wider text-steel">Role</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-wider text-steel">Shift</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-wider text-steel text-right">Avg Score</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-wider text-steel text-right">Conversations</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {salespeople.map((sp) => {
                  const perf = performances.get(sp.id);
                  return (
                    <TableRow key={sp.id}>
                      <TableCell>
                        <Link
                          href={`/salesperson/${sp.id}`}
                          className="font-medium text-primary hover:underline"
                        >
                          {sp.name}
                        </Link>
                      </TableCell>
                      <TableCell className="text-steel">{sp.role || "—"}</TableCell>
                      <TableCell className="text-steel">{sp.shift || "—"}</TableCell>
                      <TableCell className="text-right">
                        {perf?.avg_overall_score != null ? (
                          <Badge
                            variant="outline"
                            className={
                              perf.avg_overall_score >= 80
                                ? "border-brand-green/30 text-brand-green-deep bg-brand-green-soft font-mono"
                                : perf.avg_overall_score >= 60
                                ? "border-brand-warn/30 text-amber-700 bg-amber-50 font-mono"
                                : "border-brand-error/20 text-destructive bg-destructive/10 font-mono"
                            }
                          >
                            {perf.avg_overall_score.toFixed(0)}
                          </Badge>
                        ) : (
                          <span className="text-steel font-mono text-sm">—</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm">
                        {perf?.total_conversations ?? 0}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Inbox className="h-10 w-10 text-stone/40 mb-3" />
              <p className="text-sm font-medium text-steel">No salespeople in this store</p>
              <p className="text-xs text-stone mt-1">Add team members to start tracking performance.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
