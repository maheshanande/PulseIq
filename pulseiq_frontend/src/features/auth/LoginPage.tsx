import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Activity, ArrowRight, BrainCircuit, Fingerprint, Radar, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ApiError, consumeSessionMessage, pulseIqApi, saveSession } from "@/lib/api";

const signalPoints = [
  { label: "Signal extraction", value: "Live" },
  { label: "Role-aware access", value: "Enforced" },
  { label: "Operational memory", value: "Ready" },
];

export function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [sessionMessage] = useState(() => consumeSessionMessage());
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? "/";

  const mutation = useMutation({
    mutationFn: () => pulseIqApi.login(username, password),
    onSuccess: (response) => {
      saveSession(response);
      navigate(response.must_reset_password ? "/reset-password" : from, { replace: true });
    },
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (username && password) mutation.mutate();
  }

  const loginErrorMessage =
    mutation.error instanceof ApiError && mutation.error.status === 401
      ? "Your employer needs to add you to the PulseIQ sandbox before you can sign in."
      : mutation.error?.message;

  return (
    <main className="relative min-h-screen overflow-hidden bg-background px-4 py-8">
      <div className="fixed inset-0 -z-10 surface-grid opacity-35" />
      <div className="fixed inset-0 -z-10 bg-[linear-gradient(135deg,rgba(36,83,122,0.22),transparent_42%,rgba(93,213,183,0.1)),repeating-linear-gradient(0deg,rgba(255,255,255,0.025)_0px,rgba(255,255,255,0.025)_1px,transparent_1px,transparent_10px)]" />

      <div className="mx-auto grid min-h-[calc(100vh-4rem)] w-full max-w-6xl items-center gap-8 lg:grid-cols-[minmax(0,1fr)_440px]">
        <section className="space-y-8">
          <div className="inline-flex items-center gap-2 rounded-md border border-primary/20 bg-primary/10 px-3 py-2 text-xs font-medium uppercase tracking-normal text-primary">
            <Activity className="h-4 w-4" />
            PulseIQ Command Layer
          </div>
          <div className="max-w-3xl space-y-5">
            <h1 className="text-4xl font-semibold tracking-normal text-foreground sm:text-5xl lg:text-6xl">
              PulseIQ turns daily updates into operational intelligence.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">
              A focused AI workspace for facilities, teams, and leaders to capture frontline signals, understand what changed, and act with confidence.
            </p>
          </div>

          <div className="grid max-w-3xl gap-3 sm:grid-cols-3">
            {signalPoints.map((point) => (
              <div key={point.label} className="rounded-lg border border-border bg-card/70 p-4 shadow-2xl shadow-black/20">
                <div className="text-xs text-muted-foreground">{point.label}</div>
                <div className="mt-2 text-sm font-semibold text-foreground">{point.value}</div>
              </div>
            ))}
          </div>

          <div className="max-w-3xl rounded-lg border border-primary/15 bg-background/55 p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md border border-primary/20 bg-primary/10 text-primary">
                <BrainCircuit className="h-6 w-6" />
              </div>
              <div>
                <div className="text-sm font-medium text-foreground">Scope</div>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">
                  Capture employee updates, protect role-based workflows, and convert unstructured messages into timeline-ready business context.
                </p>
              </div>
            </div>
          </div>
        </section>

        <Card className="w-full border-primary/15 bg-card/85 shadow-2xl shadow-black/40 backdrop-blur">
          <CardHeader>
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-md border border-primary/20 bg-primary/10 text-primary">
                <Sparkles className="h-5 w-5" />
              </div>
              <div className="flex items-center gap-2 rounded-md border border-border bg-background/60 px-3 py-2 text-xs text-muted-foreground">
                <Radar className="h-3.5 w-3.5 text-primary" />
                AI signal online
              </div>
            </div>
            <CardTitle className="text-2xl">Welcome back</CardTitle>
            <p className="text-sm leading-6 text-muted-foreground">Sign in with your PulseIQ backend account to continue.</p>
          </CardHeader>
          <CardContent>
            {sessionMessage ? (
              <div className="mb-4 rounded-md border border-amber-400/20 bg-amber-400/10 p-3 text-sm text-amber-100">{sessionMessage}</div>
            ) : null}
            <form className="space-y-3" onSubmit={onSubmit}>
              <Input value={username} onChange={(event) => setUsername(event.target.value)} type="email" placeholder="admin@example.com" />
              <Input value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="Password" />
              {loginErrorMessage ? <p className="text-sm text-red-200">{loginErrorMessage}</p> : null}
              <Button className="w-full" disabled={!username || !password || mutation.isPending}>
                <Fingerprint className="h-4 w-4" />
                {mutation.isPending ? "Signing in..." : "Sign in"}
                <ArrowRight className="h-4 w-4" />
              </Button>
            </form>
            <div className="mt-5 border-t border-border pt-4 text-center text-sm text-muted-foreground">
              Forgot password?{" "}
              <Link className="font-medium text-primary hover:underline" to="/forgot-password">
                Recover access
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
