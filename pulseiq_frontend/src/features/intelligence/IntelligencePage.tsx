import { useMutation } from "@tanstack/react-query";
import { Brain, Send } from "lucide-react";
import { useState } from "react";
import { IntelligenceCard } from "@/components/domain/IntelligenceCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { pulseIqApi } from "@/lib/api";
import type { QueryResponse } from "@/lib/types";

const prompts = ["What is blocking ACME right now?", "What is pending this week?", "Which customers have active issues?"];

type QueryResult = {
  question: string;
  response: QueryResponse;
};

export function IntelligencePage() {
  const [question, setQuestion] = useState("");
  const [results, setResults] = useState<QueryResult[]>([]);
  const mutation = useMutation({
    mutationFn: pulseIqApi.query,
    onSuccess: (response, askedQuestion) => {
      setResults((current) => [{ question: askedQuestion, response }, ...current]);
      setQuestion("");
    },
  });

  return (
    <div className="space-y-5">
      <section className="flex flex-col gap-2">
        <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.2em] text-primary">
          <Brain className="h-4 w-4" />
          Query Workspace
        </div>
        <h1 className="text-2xl font-semibold tracking-normal">Ask questions against tenant messages.</h1>
        <p className="text-sm leading-6 text-muted-foreground">Calls <code className="rounded bg-secondary px-1.5 py-0.5 text-foreground">POST /query</code> and renders the structured response.</p>
      </section>

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col gap-3 lg:flex-row">
            <Input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && question.trim()) {
                  mutation.mutate(question.trim());
                }
              }}
              placeholder="What is blocking ACME right now?"
            />
            <Button disabled={!question.trim() || mutation.isPending} onClick={() => mutation.mutate(question.trim())}>
              <Send className="h-4 w-4" />
              Ask
            </Button>
          </div>
          {mutation.error ? <p className="mt-3 text-sm text-red-200">{mutation.error.message}</p> : null}
          <div className="mt-3 flex flex-wrap gap-2">
            {prompts.map((prompt) => (
              <Button key={prompt} variant="outline" size="sm" onClick={() => setQuestion(prompt)}>
                {prompt}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      <section className="space-y-4">
        {results.map((result) => (
          <IntelligenceCard key={`${result.question}-${result.response.executive_summary}`} question={result.question} response={result.response} />
        ))}
        {!results.length ? (
          <Card>
            <CardContent className="p-6 text-sm text-muted-foreground">No queries yet. Submit a few messages first, then ask a business question.</CardContent>
          </Card>
        ) : null}
      </section>
    </div>
  );
}
