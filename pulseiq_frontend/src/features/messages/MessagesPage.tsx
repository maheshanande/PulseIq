import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { pulseIqApi } from "@/lib/api";

export function MessagesPage() {
  const { data = [], error, isLoading } = useQuery({ queryKey: ["messages"], queryFn: pulseIqApi.getMessages });
  const [search, setSearch] = useState("");
  const [date, setDate] = useState("");

  const filtered = useMemo(
    () =>
      data.filter((message) => {
        const matchesSearch =
          !search ||
          message.content.toLowerCase().includes(search.toLowerCase()) ||
          message.id.toLowerCase().includes(search.toLowerCase()) ||
          (message.user_id ?? "").toLowerCase().includes(search.toLowerCase());
        const matchesDate = !date || message.created_at.startsWith(date);
        return matchesSearch && matchesDate;
      }),
    [data, date, search],
  );

  return (
    <div className="space-y-5">
      <section>
        <h1 className="text-2xl font-semibold tracking-normal">Messages</h1>
        <p className="mt-2 text-sm text-muted-foreground">Recent tenant messages from <code className="rounded bg-secondary px-1.5 py-0.5 text-foreground">GET /messages</code>.</p>
      </section>
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search content, message ID, user ID" />
          <Input value={date} onChange={(event) => setDate(event.target.value)} type="date" aria-label="Date" />
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-0">
          {isLoading ? <div className="p-4 text-sm text-muted-foreground">Loading messages...</div> : null}
          {error ? <div className="p-4 text-sm text-red-200">{error.message}</div> : null}
          <div className="divide-y divide-border">
            {filtered.map((message) => (
              <div key={message.id} className="grid gap-3 p-4 md:grid-cols-[180px_minmax(0,1fr)] md:items-start">
                <div>
                  <div className="text-sm font-medium text-foreground">{formatDate(message.created_at)}</div>
                  <div className="mt-1 truncate text-xs text-muted-foreground">{message.user_id ?? "System"}</div>
                </div>
                <div>
                  <p className="text-sm leading-6 text-foreground">{message.content}</p>
                  <div className="mt-2 truncate text-xs text-muted-foreground">{message.id}</div>
                </div>
              </div>
            ))}
          </div>
          {!filtered.length && !isLoading ? <div className="p-4 text-sm text-muted-foreground">No messages found.</div> : null}
        </CardContent>
      </Card>
    </div>
  );
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}
