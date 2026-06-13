import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Send, Sparkles } from "lucide-react";
import { Navigate } from "react-router-dom";
import { useState } from "react";
import { TimelineEvent } from "@/components/domain/TimelineEvent";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { getCurrentRole, pulseIqApi } from "@/lib/api";

const updatePrompts = [
  {
    label: "Order shipped",
    text: "Order #____ shipped to ____ at ____.",
  },
  {
    label: "Payment pending",
    text: "Payment pending from ____ for invoice/order ____ since ____.",
  },
  {
    label: "Machine issue",
    text: "Line/Machine ____ is down for ____ because ____.",
  },
  {
    label: "Customer blocked",
    text: "Customer ____ is blocked by ____ and needs ____.",
  },
  {
    label: "Stock update",
    text: "Stock for ____ is ____ and expected refill/dispatch is ____.",
  },
];

export function OverviewPage() {
  const role = getCurrentRole();

  if (role === "super_admin") {
    return <Navigate to="/settings" replace />;
  }

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <section className="space-y-4">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.2em] text-primary">
            <Sparkles className="h-4 w-4" />
            Daily Update
          </div>
          <h1 className="text-3xl font-semibold tracking-normal text-foreground">Send a clean operational update.</h1>
          <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
            Pick a starting point, complete the details, and submit. PulseIQ will extract the business signal in the background.
          </p>
        </div>
        <EmployeeUpdateConsole />
        <EmployeeMessageTimeline />
      </section>
    </div>
  );
}

function EmployeeUpdateConsole() {
  const [content, setContent] = useState("");
  const [submitted, setSubmitted] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: pulseIqApi.createMessage,
    onSuccess: (message) => {
      setSubmitted(message.content);
      setContent("");
      void queryClient.invalidateQueries({ queryKey: ["messages"] });
    },
  });

  return (
    <Card className="overflow-hidden">
      <CardContent className="space-y-5 p-5">
        <div className="flex flex-wrap gap-2">
          {updatePrompts.map((prompt) => (
            <Button key={prompt.label} variant="outline" size="sm" onClick={() => setContent(prompt.text)}>
              {prompt.label}
            </Button>
          ))}
        </div>

        <div className="rounded-lg border border-border bg-background/55 p-4">
          <div className="mb-3 flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary/10 text-xs font-semibold text-primary">P</span>
            <div>
              <div className="text-sm font-medium text-foreground">PulseIQ intake</div>
              <div className="text-xs text-muted-foreground">Write like a normal work update.</div>
            </div>
          </div>
          <Textarea
            value={content}
            onChange={(event) => setContent(event.target.value)}
            onKeyDown={(event) => {
              if ((event.metaKey || event.ctrlKey) && event.key === "Enter" && content.trim()) {
                mutation.mutate(content.trim());
              }
            }}
            className="min-h-[150px] border-border bg-card text-base leading-7"
            placeholder="Example: Customer ACME reported that integration testing is blocked by missing API credentials."
          />
          {mutation.error ? <p className="mt-3 text-sm text-red-200">{mutation.error.message}</p> : null}
          <div className="mt-4 flex items-center justify-between gap-3">
            <p className="text-xs text-muted-foreground">Submit with Ctrl/⌘ Enter</p>
            <Button disabled={!content.trim() || mutation.isPending} onClick={() => mutation.mutate(content.trim())}>
              <Send className="h-4 w-4" />
              {mutation.isPending ? "Submitting..." : "Submit update"}
            </Button>
          </div>
        </div>

        {submitted ? (
          <div className="flex gap-3 rounded-lg border border-emerald-400/20 bg-emerald-400/10 p-4">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-200" />
            <div>
              <div className="text-sm font-medium text-emerald-100">Update submitted</div>
              <p className="mt-1 text-sm leading-6 text-emerald-100/80">{submitted}</p>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function EmployeeMessageTimeline() {
  const { data = [], error, isLoading } = useQuery({ queryKey: ["messages"], queryFn: pulseIqApi.getMessages });
  const recentMessages = [...data]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  return (
    <Card>
      <CardContent className="p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-foreground">Recent update timeline</h2>
            <p className="mt-1 text-xs text-muted-foreground">Your latest submitted operational messages.</p>
          </div>
          <span className="rounded-md border border-border bg-background/60 px-2 py-1 text-xs text-muted-foreground">
            {recentMessages.length} shown
          </span>
        </div>
        {isLoading ? <p className="text-sm text-muted-foreground">Loading recent updates...</p> : null}
        {error ? <p className="text-sm text-red-200">{error.message}</p> : null}
        {recentMessages.map((message, index) => (
          <TimelineEvent
            key={message.id}
            time={message.created_at}
            title="Update submitted"
            description={message.content}
            isLast={index === recentMessages.length - 1}
          />
        ))}
        {!recentMessages.length && !isLoading ? <p className="text-sm text-muted-foreground">No updates submitted yet.</p> : null}
      </CardContent>
    </Card>
  );
}
