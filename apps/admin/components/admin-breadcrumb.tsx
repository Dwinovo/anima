"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

const PAGE_LABELS: Record<string, string> = {
  overview: "总览",
  sessions: "会话",
};

function getCurrentPageLabel(pathname: string) {
  const segment = pathname.split("/").filter(Boolean)[0] ?? "overview";

  return PAGE_LABELS[segment] ?? segment;
}

export function AdminBreadcrumb() {
  const pathname = usePathname();
  const currentPageLabel = getCurrentPageLabel(pathname);

  return (
    <Breadcrumb className="w-fit">
      <BreadcrumbList className="gap-3 text-lg sm:text-xl">
        <BreadcrumbItem>
          <BreadcrumbLink asChild className="font-heading">
            <Link
              href="/overview"
              className="breadcrumb-title-hover type-title leading-none"
            >
              Anima
            </Link>
          </BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator className="[&>svg]:size-4.5" />
        <BreadcrumbItem>
          <BreadcrumbPage className="breadcrumb-title-hover type-title font-heading leading-none">
            {currentPageLabel}
          </BreadcrumbPage>
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>
  );
}
