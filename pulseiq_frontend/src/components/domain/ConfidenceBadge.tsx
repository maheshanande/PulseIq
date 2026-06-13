import { ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function ConfidenceBadge({ label, score }: { label: string; score?: number }) {
  const normalized = label.toLowerCase();
  const variant = normalized === "high" ? "success" : normalized === "medium" ? "warning" : "danger";
  const Icon = normalized === "high" ? ShieldCheck : normalized === "medium" ? ShieldQuestion : ShieldAlert;

  return (
    <Badge variant={variant} className="gap-1.5">
      <Icon className="h-3.5 w-3.5" />
      {label}
      {typeof score === "number" ? ` · ${Math.round(score * 100)}%` : null}
    </Badge>
  );
}
