import { Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function HealthScoreCard({ status }: { status: string }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle>API Health</CardTitle>
          <Activity className="h-4 w-4 text-primary" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-semibold tracking-normal">{status}</div>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">Connected to the PulseIQ backend health endpoint.</p>
      </CardContent>
    </Card>
  );
}
