"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GraduationCap } from "lucide-react";

export default function CoachingPage() {
  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Coaching Dashboard</h1>
        <p className="text-muted-foreground">AI-powered coaching recommendations</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GraduationCap className="h-4 w-4" />
            Skill Scores & Trends
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Coaching dashboard will display skill scores, improvement areas, and historical trends
            once recording analysis data is available. This feature is planned for Sprint 5.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
