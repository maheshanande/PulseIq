import { useQuery } from "@tanstack/react-query";
import { TimelineEvent } from "@/components/domain/TimelineEvent";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { pulseIqApi } from "@/lib/api";

export function TimelinePage() {
  const { data = [], error, isLoading } = useQuery({ queryKey: ["messages"], queryFn: pulseIqApi.getMessages });
  const sorted = [...data].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

  return (
    <div className="space-y-5">
      <section>
        <h1 className="text-2xl font-semibold tracking-normal">Message Timeline</h1>
        <p className="mt-2 text-sm text-muted-foreground">Chronological view of submitted messages. Extracted event timelines appear inside query responses.</p>
      </section>
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? <p className="text-sm text-muted-foreground">Loading timeline...</p> : null}
          {error ? <p className="text-sm text-red-200">{error.message}</p> : null}
          {sorted.map((message, index) => (
            <TimelineEvent
              key={message.id}
              time={message.created_at}
              title="Message submitted"
              description={message.content}
              entity={message.user_id ?? "Tenant"}
              isLast={index === sorted.length - 1}
            />
          ))}
          {!sorted.length && !isLoading ? <p className="text-sm text-muted-foreground">No messages yet.</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}
