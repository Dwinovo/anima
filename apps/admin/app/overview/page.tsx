import { LayoutGrid } from "lucide-react";

export default function OverviewPage() {
  return (
    <section className="space-y-2">
      <div className="flex items-center gap-3">
        <LayoutGrid className="size-7 text-foreground" />
        <h2 className="type-title text-3xl leading-none">总览</h2>
      </div>
    </section>
  );
}
