import { useNavigate } from "react-router-dom";
import { KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ForgotPasswordPage() {
  const navigate = useNavigate();

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="fixed inset-0 -z-10 surface-grid opacity-30" />
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-md border border-primary/20 bg-primary/10 text-primary">
            <KeyRound className="h-5 w-5" />
          </div>
          <CardTitle className="text-xl">Recover PulseIQ access</CardTitle>
          <p className="text-sm leading-6 text-muted-foreground">
            PulseIQ accounts are managed by your employer. Ask your facility admin or PulseIQ owner to add you to the sandbox or issue a new temporary password.
          </p>
        </CardHeader>
        <CardContent>
          <Button className="w-full" onClick={() => navigate("/login")}>
            Back to sign in
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
