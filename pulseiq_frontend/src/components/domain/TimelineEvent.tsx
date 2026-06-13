import { motion } from "framer-motion";
import { CircleDot } from "lucide-react";
import { EntityTag } from "@/components/domain/EntityTag";

type TimelineEventProps = {
  time: string;
  title: string;
  description?: string;
  entity?: string;
  isLast?: boolean;
};

export function TimelineEvent({ time, title, description, entity, isLast = false }: TimelineEventProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-[92px_24px_minmax(0,1fr)] gap-4"
    >
      <div className="pt-1 text-xs font-medium text-muted-foreground">{formatTime(time)}</div>
      <div className="relative flex justify-center">
        {!isLast && <div className="absolute top-8 h-full w-px bg-border" />}
        <div className="z-10 flex h-7 w-7 items-center justify-center rounded-full border border-primary/30 bg-background text-primary">
          <CircleDot className="h-3.5 w-3.5" />
        </div>
      </div>
      <div className="pb-6">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          {entity ? <EntityTag value={entity} /> : null}
        </div>
        {description ? <p className="mt-1 text-sm leading-6 text-muted-foreground">{description}</p> : null}
      </div>
    </motion.div>
  );
}

function formatTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
