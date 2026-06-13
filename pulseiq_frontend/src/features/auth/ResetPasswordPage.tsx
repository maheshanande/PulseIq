import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { pulseIqApi } from "@/lib/api";

export function ResetPasswordPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const navigate = useNavigate();
  const mutation = useMutation({
    mutationFn: () => pulseIqApi.resetPassword(currentPassword, newPassword),
    onSuccess: () => {
      localStorage.setItem("pulseiq_must_reset_password", "false");
      navigate("/", { replace: true });
    },
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (currentPassword && newPassword) mutation.mutate();
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="fixed inset-0 -z-10 surface-grid opacity-30" />
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-xl">Reset password</CardTitle>
          <p className="text-sm leading-6 text-muted-foreground">Your account must set a new password before submitting messages.</p>
        </CardHeader>
        <CardContent>
          <form className="space-y-3" onSubmit={onSubmit}>
            <Input value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} type="password" placeholder="Current password" />
            <Input value={newPassword} onChange={(event) => setNewPassword(event.target.value)} type="password" placeholder="New password" />
            {mutation.error ? <p className="text-sm text-red-200">{mutation.error.message}</p> : null}
            <Button className="w-full" disabled={!currentPassword || !newPassword || mutation.isPending}>
              {mutation.isPending ? "Updating..." : "Update password"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
