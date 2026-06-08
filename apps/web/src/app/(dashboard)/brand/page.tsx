"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { Brand, Store as StoreType, SalespersonPerformance } from "@samaa/shared";
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
import { Store as StoreIcon, Users, Mic, TrendingUp, AlertTriangle } from "lucide-react";
import Link from "next/link";

export default function BrandDashboardPage() {
  const { data: stores } = useQuery({
    queryKey: ["stores"],
    queryFn: () => api.get<StoreType[]>("/stores"),
  });

  const storeCount = stores?.length ?? 0;

  // Fetch salespeople to get total count
  const { data: salespeople } = useQuery({
    queryKey: ["salespeople"],
    queryFn: () => api.get<SalespersonPerformance[]>("/salespeople"),
  });

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Brand Dashboard</h1>
        <p className="text-muted-foreground">Overview of your brand performance</p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Stores"
          value={storeCount}
          icon={StoreIcon}
          description="Active retail locations"
        />
        <KPICard
          title="Salespeople"
          value={salespeople?.length ?? 0}
          icon={Users}
          description="Across all stores"
        />
        <KPICard
          title="Conversations"
          value="—"
          icon={Mic}
          description="Detected this week"
        />
        <KPICard
          title="Avg Conversion"
          value="—"
          icon={TrendingUp}
          description="Sales conversion rate"
        />
      </div>

      {/* Store Ranking Table */}
      <Card>
        <CardHeader>
          <CardTitle>Store Performance Ranking</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Store</TableHead>
                <TableHead>Location</TableHead>
                <TableHead className="text-right">Salespeople</TableHead>
                <TableHead className="text-right">Avg Score</TableHead>
                <TableHead className="text-right">Conversations</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {stores?.map((store: StoreType) => (
                <TableRow key={store.id}>
                  <TableCell>
                    <Link
                      href={`/store/${store.id}`}
                      className="font-medium text-primary hover:underline"
                    >
                      {store.name}
                    </Link>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {store.location || "—"}
                  </TableCell>
                  <TableCell className="text-right">—</TableCell>
                  <TableCell className="text-right">—</TableCell>
                  <TableCell className="text-right">—</TableCell>
                </TableRow>
              )) ?? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    No stores found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Coaching Alerts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            Coaching Alerts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Coaching alerts will appear here when AI analysis identifies salespeople who need improvement.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
