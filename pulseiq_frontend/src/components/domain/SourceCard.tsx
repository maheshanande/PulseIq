import { FileText } from "lucide-react";
import type { QueryResponse } from "@/lib/types";

export function SourceCard({ source }: { source: QueryResponse["sources"][number] }) {
  return (
    <div className="rounded-md border border-border bg-background/55 p-3">
      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
        <FileText className="h-3.5 w-3.5" />
        {source.submitted_by}
      </div>
      <p className="mt-2 line-clamp-3 text-sm leading-6 text-foreground">{source.content}</p>
      <div className="mt-2 truncate text-xs text-muted-foreground">{source.message_id}</div>
    </div>
  );
}
