import { motion } from "framer-motion";
import { CircleDot } from "lucide-react";
import { ConfidenceBadge } from "@/components/domain/ConfidenceBadge";
import { SourceCard } from "@/components/domain/SourceCard";
import { TimelineEvent } from "@/components/domain/TimelineEvent";
import { Card } from "@/components/ui/card";
import type { QueryResponse } from "@/lib/types";

export function IntelligenceCard({ question, response }: { question: string; response: QueryResponse }) {
  return (
    <motion.article initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
      <Card className="overflow-hidden">
        <div className="border-b border-border px-5 py-4">
          <div className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">Question</div>
          <h2 className="mt-2 text-xl font-semibold tracking-normal text-foreground">{question}</h2>
        </div>
        <div className="grid gap-0 lg:grid-cols-[minmax(0,1.25fr)_minmax(320px,.75fr)]">
          <div className="space-y-6 p-5">
            <section>
              <h3 className="text-sm font-semibold text-foreground">Executive Summary</h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{response.executive_summary}</p>
            </section>
            {response.assessment ? (
              <section>
                <h3 className="text-sm font-semibold text-foreground">Assessment</h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{response.assessment}</p>
              </section>
            ) : null}
            <section>
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-sm font-semibold text-foreground">Sources</h3>
                <ConfidenceBadge label={response.confidence.label} score={response.confidence.score} />
              </div>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                {response.sources.map((source) => (
                  <SourceCard key={source.message_id} source={source} />
                ))}
              </div>
            </section>
          </div>
          <aside className="border-t border-border bg-background/40 p-5 lg:border-l lg:border-t-0">
            <div className="rounded-lg border border-border bg-card p-4">
              <div className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">Current Status</div>
              <div className="mt-3 flex items-center gap-2 text-sm font-semibold text-primary">
                <CircleDot className="h-4 w-4" />
                {response.current_status ?? "No active status"}
              </div>
            </div>
            <div className="mt-5">
              <h3 className="text-sm font-semibold text-foreground">Timeline</h3>
              <div className="mt-3">
                {response.timeline.length ? (
                  response.timeline.map((event, index) => (
                    <TimelineEvent
                      key={`${event.time}-${event.event}`}
                      time={event.time}
                      title={event.event}
                      description={`Reported by ${event.reported_by}`}
                      entity={event.entity_name}
                      isLast={index === response.timeline.length - 1}
                    />
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No timeline events returned.</p>
                )}
              </div>
            </div>
          </aside>
        </div>
      </Card>
    </motion.article>
  );
}
