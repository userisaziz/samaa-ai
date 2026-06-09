import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  description?: string;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

export function KPICard({ title, value, description, icon: Icon, trend }: KPICardProps) {
  return (
    <Card className="shadow-[0_1px_3px_rgba(0,0,0,0.04),0_1px_2px_rgba(0,0,0,0.06)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-shadow duration-200">
      <CardHeader className="flex flex-row items-center justify-between pb-1">
        <CardTitle className="text-sm font-medium text-steel">{title}</CardTitle>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-green-soft">
          <Icon className="h-4.5 w-4.5 text-brand-green-deep" />
        </div>
      </CardHeader>
      <CardContent className="space-y-1">
        <div className="text-2xl font-semibold tracking-tight text-ink font-mono">{value}</div>
        {description && (
          <p className="text-xs text-steel">{description}</p>
        )}
        {trend && (
          <div className="flex items-center gap-1.5 mt-0.5">
            {trend.isPositive ? (
              <TrendingUp className="h-3.5 w-3.5 text-brand-green-deep" />
            ) : (
              <TrendingDown className="h-3.5 w-3.5 text-destructive" />
            )}
            <span
              className={`text-xs font-medium font-mono ${
                trend.isPositive ? "text-brand-green-deep" : "text-destructive"
              }`}
            >
              {trend.isPositive ? "+" : ""}
              {trend.value}%
            </span>
            <span className="text-xs text-steel">from last period</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
