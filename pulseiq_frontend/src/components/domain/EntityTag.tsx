import { Badge } from "@/components/ui/badge";

export function EntityTag({ value }: { value: string }) {
  return <Badge variant="muted">{value}</Badge>;
}
