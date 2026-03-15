import { MessagesSquare } from "lucide-react";

export default function SessionsPage() {
  return (
    <section className="space-y-2">
      <div className="flex items-center gap-3">
        <MessagesSquare className="size-7 text-foreground" />
        <h2 className="type-title text-3xl leading-none">会话</h2>
      </div>
    </section>
  );
}
