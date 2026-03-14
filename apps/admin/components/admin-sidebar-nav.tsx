"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutGrid, MessagesSquare } from "lucide-react";

import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";

export function AdminSidebarNav() {
  const pathname = usePathname();

  const isOverviewActive = pathname === "/" || pathname === "/overview";
  const isSessionsActive = pathname.startsWith("/sessions");
  const navItemClass = "";

  return (
    <SidebarGroup>
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton
            asChild
            isActive={isOverviewActive}
            className={cn(
              navItemClass,
              isOverviewActive && "bg-main text-main-foreground outline-border",
            )}
          >
            <Link href="/overview">
              <LayoutGrid />
              <span>总览</span>
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
        <SidebarMenuItem>
          <SidebarMenuButton
            asChild
            isActive={isSessionsActive}
            className={cn(
              navItemClass,
              isSessionsActive && "bg-main text-main-foreground outline-border",
            )}
          >
            <Link href="/sessions">
              <MessagesSquare />
              <span>会话</span>
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarGroup>
  );
}
