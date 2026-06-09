"use client";

import { useState } from "react";
import type { Conversation, ConversationAnalysis, StructuredObjection } from "@samaa/shared";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Eye,
  XCircle,
  AlertTriangle,
  Package,
  FileText,
  Brain,
  ChevronDown,
  ChevronRight,
  Swords,
  DollarSign,
  Inbox,
} from "lucide-react";

interface AnalysisDetailProps {
  conversation: Conversation;
  analysis: ConversationAnalysis | null;
}

function isStructuredObjection(o: unknown): o is StructuredObjection {
  return typeof o === "object" && o !== null && "category" in o;
}

function SectionCard({
  title,
  icon: Icon,
  iconColor,
  children,
  defaultOpen = true,
}: {
  title: string;
  icon: React.ElementType;
  iconColor?: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <Card className="shadow-[0_1px_3px_rgba(0,0,0,0.04),0_1px_2px_rgba(0,0,0,0.06)]">
      <CardHeader
        className="cursor-pointer select-none pb-3"
        onClick={() => setOpen((p) => !p)}
      >
        <div className="flex items-center gap-2">
          {open ? (
            <ChevronDown className="h-4 w-4 text-steel" />
          ) : (
            <ChevronRight className="h-4 w-4 text-steel" />
          )}
          <Icon className={`h-4 w-4 ${iconColor ?? "text-steel"}`} />
          <CardTitle className="text-sm font-medium text-steel">{title}</CardTitle>
        </div>
      </CardHeader>
      {open && <CardContent className="pt-0">{children}</CardContent>}
    </Card>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-2 py-3 text-sm text-stone">
      <Inbox className="h-4 w-4" />
      <span>{message}</span>
    </div>
  );
}

export function AnalysisDetail({ conversation, analysis }: AnalysisDetailProps) {
  if (!analysis) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <p className="text-sm text-steel">Analysis pending for this conversation</p>
        </CardContent>
      </Card>
    );
  }

  const customerExpectation = analysis.customer_expectation || analysis.intent;
  const hasObjections = analysis.objections && analysis.objections.length > 0;
  const hasProducts = analysis.products && analysis.products.length > 0;
  const hasCompetitors = analysis.competitors && analysis.competitors.length > 0;
  const isLost = analysis.outcome === "LOST";

  return (
    <div className="space-y-3">
      {/* 1. Customer Expectation */}
      <SectionCard title="Customer Expectation" icon={Eye} iconColor="text-blue-500">
        {customerExpectation ? (
          <p className="text-sm text-ink leading-relaxed">{customerExpectation}</p>
        ) : (
          <EmptyState message="No customer expectation data available" />
        )}
      </SectionCard>

      {/* 2. Reason for Loss of Sale */}
      {isLost && (
        <SectionCard
          title="Reason for Loss of Sale"
          icon={XCircle}
          iconColor="text-destructive"
        >
          {analysis.loss_reason ? (
            <div className="rounded-lg border border-destructive/15 bg-destructive/[0.03] p-3">
              <p className="text-sm text-ink leading-relaxed">{analysis.loss_reason}</p>
            </div>
          ) : (
            <EmptyState message="No specific loss reason recorded" />
          )}
        </SectionCard>
      )}

      {/* 3. Customer Objections */}
      <SectionCard title="Customer Objections" icon={AlertTriangle} iconColor="text-amber-500">
        {hasObjections ? (
          <div className="overflow-x-auto -mx-6 sm:mx-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-wider text-steel w-[120px]">
                    Category
                  </TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-wider text-steel">
                    Issue
                  </TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-wider text-steel">
                    Response
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {analysis.objections.map((o, i) => {
                  if (isStructuredObjection(o)) {
                    return (
                      <TableRow key={i}>
                        <TableCell>
                          <Badge variant="outline" className="text-[11px] font-mono">
                            {o.category}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-ink">{o.issue}</TableCell>
                        <TableCell className="text-sm text-steel">{o.response || "—"}</TableCell>
                      </TableRow>
                    );
                  }
                  // Legacy string objection
                  return (
                    <TableRow key={i}>
                      <TableCell>
                        <Badge variant="outline" className="text-[11px] font-mono">
                          Other
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-ink" colSpan={2}>
                        {o}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        ) : (
          <EmptyState message="No objections recorded" />
        )}
      </SectionCard>

      {/* 4. Product Details */}
      <SectionCard title="Product Details" icon={Package} iconColor="text-emerald-500">
        {hasProducts || analysis.budget || hasCompetitors ? (
          <div className="space-y-3">
            {/* Products */}
            {hasProducts && (
              <div>
                <p className="text-xs font-medium text-steel mb-1.5">Products Discussed</p>
                <div className="flex flex-wrap gap-1.5">
                  {analysis.products.map((p, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">
                      {p}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Budget */}
            {analysis.budget && (
              <div className="flex items-center gap-1.5">
                <DollarSign className="h-3.5 w-3.5 text-steel" />
                <span className="text-sm text-ink">
                  <span className="font-medium">Budget:</span> {analysis.budget}
                </span>
              </div>
            )}

            {/* Competitors */}
            {hasCompetitors && (
              <div className="flex items-center gap-1.5">
                <Swords className="h-3.5 w-3.5 text-steel" />
                <span className="text-sm text-ink">
                  <span className="font-medium">Competitors:</span>{" "}
                  {analysis.competitors.join(", ")}
                </span>
              </div>
            )}
          </div>
        ) : (
          <EmptyState message="No product details recorded" />
        )}
      </SectionCard>

      {/* 5. Summary */}
      <SectionCard title="Summary" icon={FileText} iconColor="text-blue-500">
        {analysis.summary ? (
          <p className="text-sm text-ink leading-relaxed">{analysis.summary}</p>
        ) : (
          <EmptyState message="No summary available" />
        )}
      </SectionCard>

      {/* 6. SOP / Coaching Notes */}
      <SectionCard title="SOP" icon={Brain} iconColor="text-amber-600">
        {analysis.coaching_notes ? (
          <div className="rounded-lg border border-amber-100 bg-amber-50 p-3">
            <p className="text-sm text-amber-900 leading-relaxed">
              {analysis.coaching_notes}
            </p>
          </div>
        ) : (
          <EmptyState message="No SOP / coaching notes available" />
        )}
      </SectionCard>
    </div>
  );
}
