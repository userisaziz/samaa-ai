"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api-client";
import type { SalespersonPerformance } from "@samaa/shared";
import { KPICard } from "@/components/kpi-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Award,
  TrendingUp,
  TrendingDown,
  Target,
  AlertTriangle,
  Brain,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
} from "lucide-react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
} from "recharts";

// Mock trend data (will be replaced with real API data in Sprint 6)
const mockTrendData = [
  { week: "W1", score: 62 },
  { week: "W2", score: 65 },
  { week: "W3", score: 61 },
  { week: "W4", score: 68 },
  { week: "W5", score: 72 },
  { week: "W6", score: 70 },
  { week: "W7", score: 74 },
  { week: "W8", score: 76 },
];

function ScoreTrendArrow({ current, previous }: { current: number; previous: number }) {
  const diff = current - previous;
  if (diff > 0) {
    return (
      <span className="flex items-center gap-0.5 text-xs text-green-600">
        <ArrowUpRight className="h-3 w-3" />
        +{diff.toFixed(0)}
      </span>
    );
  }
  if (diff < 0) {
    return (
      <span className="flex items-center gap-0.5 text-xs text-red-600">
        <ArrowDownRight className="h-3 w-3" />
        {diff.toFixed(0)}
      </span>
    );
  }
  return (
    <span className="flex items-center gap-0.5 text-xs text-muted-foreground">
      <Minus className="h-3 w-3" />
      0
    </span>
  );
}

const SKILL_LABELS: Record<string, string> = {
  avg_greeting_score: "Greeting",
  avg_discovery_score: "Discovery",
  avg_product_knowledge_score: "Product Knowledge",
  avg_objection_handling_score: "Objection Handling",
  avg_closing_score: "Closing",
};

export default function CoachingPage() {
  const { user } = useAuthStore();

  // For salesperson role, show their own performance
  // For manager/admin, this would show selected salesperson
  const salespersonId = user?.store_id; // Placeholder — in real app, this comes from route params

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Coaching Dashboard</h1>
        <p className="text-muted-foreground">AI-powered performance insights and recommendations</p>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="30d">30 Days</TabsTrigger>
          <TabsTrigger value="60d">60 Days</TabsTrigger>
          <TabsTrigger value="90d">90 Days</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-4">
          {/* Skill Scores */}
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="h-4 w-4" />
                  Skill Scores
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(SKILL_LABELS).map(([key, label]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-sm">{label}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold">—</span>
                        <ScoreTrendArrow current={0} previous={0} />
                      </div>
                    </div>
                  ))}
                  <Separator />
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Overall</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold">—</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Radar Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Skill Radar</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[250px] flex items-center justify-center text-muted-foreground text-sm">
                  Skill radar will render when analysis data is available
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Improvement Areas */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Improvement Areas
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                AI-identified improvement areas will appear here based on conversation analysis patterns.
                Specific conversation examples will be linked for targeted coaching.
              </p>
            </CardContent>
          </Card>

          {/* Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-4 w-4 text-blue-500" />
                Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Prioritized action items based on performance trends will appear here.
              </p>
            </CardContent>
          </Card>

          {/* Historical Trend */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Score Trend
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={mockTrendData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="week" className="text-xs" />
                    <YAxis domain={[0, 100]} className="text-xs" />
                    <RechartsTooltip />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="hsl(var(--primary))"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="30d" className="mt-4">
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground text-sm">
              30-day detailed view with conversation-level breakdown
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="60d" className="mt-4">
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground text-sm">
              60-day trend analysis with week-over-week comparisons
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="90d" className="mt-4">
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground text-sm">
              90-day quarterly review with comprehensive performance summary
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
