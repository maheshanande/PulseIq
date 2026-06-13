import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { pulseIqApi, saveSession } from "@/lib/api";

export function SetupSuperAdminPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [setupToken, setSetupToken] = useState("");
  const navigate = useNavigate();

  const mutation = useMutation({
    mutationFn: () => pulseIqApi.bootstrapSuperAdmin(email, password, setupToken),
    onSuccess: (response) => {
      saveSession(response);
      navigate("/settings", { replace: true });
    },
  });

  const passwordMismatch = confirmPassword.length > 0 && password !== confirmPassword;
  const passwordTooShort = password.length > 0 && password.length < 12;
  const canSubmit = email && password && confirmPassword && setupToken && !passwordMismatch && !passwordTooShort;

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (canSubmit) mutation.mutate();
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 py-8">
      <div className="fixed inset-0 -z-10 surface-grid opacity-30" />
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-md border border-primary/20 bg-primary/10 text-primary">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <CardTitle className="text-xl">Create Super Admin</CardTitle>
          <p className="text-sm leading-6 text-muted-foreground">
            Use the backend setup token from your environment to create the first platform admin.
          </p>
        </CardHeader>
        <CardContent>
          <form className="space-y-3" onSubmit={onSubmit}>
            <Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="super.admin@example.com" />
            <Input value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="Password, 12+ characters" />
            <Input value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} type="password" placeholder="Confirm password" />
            <Input value={setupToken} onChange={(event) => setSetupToken(event.target.value)} type="password" placeholder="Setup token" />
            {passwordTooShort ? <p className="text-sm text-amber-100">Password must be at least 12 characters.</p> : null}
            {passwordMismatch ? <p className="text-sm text-red-200">Passwords do not match.</p> : null}
            {mutation.error ? <p className="text-sm text-red-200">{mutation.error.message}</p> : null}
            <Button className="w-full" disabled={!canSubmit || mutation.isPending}>
              {mutation.isPending ? "Creating..." : "Create Super Admin"}
            </Button>
          </form>
          <div className="mt-4 text-center text-sm text-muted-foreground">
            Already set up?{" "}
            <Link className="font-medium text-primary hover:underline" to="/login">
              Sign in
            </Link>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
