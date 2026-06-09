"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api-client";
import type { Salesperson } from "@samaa/shared";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Users, Inbox } from "lucide-react";

export default function SalespeoplePage() {
  const { data: salespeople, isLoading } = useQuery({
    queryKey: ["salespeople"],
    queryFn: () => api.get<Salesperson[]>("/salespeople"),
  });

  return (
    <div className="space-y-6 lg:space-y-8 p-4 sm:p-6 lg:p-8">
      {/* Page Header */}
      <div className="border-b border-border pb-4 sm:pb-6">
        <h1 className="text-[22px] sm:text-[28px] font-semibold tracking-tight text-ink leading-tight">Salespeople</h1>
        <p className="mt-1 text-sm text-steel">Manage sales team members</p>
      </div>

      <Card className="shadow-[0_1px_3px_rgba(0,0,0,0.04),0_1px_2px_rgba(0,0,0,0.06)]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-4 w-4 text-steel" />
            All Salespeople
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3 py-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center gap-4 px-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-4 w-12" />
                  <Skeleton className="h-4 w-40" />
                </div>
              ))}
            </div>
          ) : salespeople && salespeople.length > 0 ? (
            <div className="overflow-x-auto -mx-6 sm:mx-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-wider text-steel">Name</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-wider text-steel">Role</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-wider text-steel">Shift</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-wider text-steel">Device #</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-wider text-steel">Email</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {salespeople.map((sp) => (
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
                    <TableCell className="text-steel font-mono text-sm">{sp.device_number || "—"}</TableCell>
                    <TableCell className="text-steel">{sp.email || "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Inbox className="h-10 w-10 text-stone/40 mb-3" />
              <p className="text-sm font-medium text-steel">No salespeople found</p>
              <p className="text-xs text-stone mt-1">Add team members to start tracking performance.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
