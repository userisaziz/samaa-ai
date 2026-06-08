"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import type { Store, Salesperson, Recording } from "@samaa/shared";
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
import { Users, Mic, TrendingUp, AlertTriangle } from "lucide-react";

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

  return (
    <div className="space-y-6 p-6">
      {/* Store Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{store?.name || "Store"}</h1>
        <p className="text-muted-foreground">{store?.location || ""}</p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Performance Score"
          value="—"
          icon={TrendingUp}
          description="Average across salespeople"
        />
        <KPICard
          title="Conversations"
          value="—"
          icon={Mic}
          description="This week"
        />
        <KPICard
          title="Salespeople"
          value={salespeople?.length ?? 0}
          icon={Users}
          description="Active in this store"
        />
        <KPICard
          title="Top Objection"
          value="—"
          icon={AlertTriangle}
          description="Most common this week"
        />
      </div>

      {/* Salesperson Performance Table */}
      <Card>
        <CardHeader>
          <CardTitle>Salesperson Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Shift</TableHead>
                <TableHead className="text-right">Avg Score</TableHead>
                <TableHead className="text-right">Conversations</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {salespeople?.map((sp) => (
                <TableRow key={sp.id}>
                  <TableCell>
                    <Link
                      href={`/salesperson/${sp.id}`}
                      className="font-medium text-primary hover:underline"
                    >
                      {sp.name}
                    </Link>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{sp.role || "—"}</TableCell>
                  <TableCell className="text-muted-foreground">{sp.shift || "—"}</TableCell>
                  <TableCell className="text-right">—</TableCell>
                  <TableCell className="text-right">—</TableCell>
                </TableRow>
              )) ?? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    No salespeople found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
