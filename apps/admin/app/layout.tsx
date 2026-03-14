import type { Metadata } from "next";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar";
import { AdminSidebarNav } from "@/components/admin-sidebar-nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Anima Admin",
  description: "Anima 管理面板",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <SidebarProvider>
          <Sidebar collapsible="icon">
            <SidebarHeader className="gap-4 p-4">
              <h1
                data-testid="sidebar-brandplate"
                className="brandplate-hover-pop logo-font-static type-title ml-10 w-fit rounded-base border-2 border-border bg-[#facc00] px-4 py-2 text-lg leading-none tracking-[0.08em] text-black shadow-shadow sm:px-5 sm:py-2.5 sm:text-xl"
              >
                Anima
              </h1>
            </SidebarHeader>
            <SidebarContent>
              <AdminSidebarNav />
            </SidebarContent>
          </Sidebar>
          <SidebarInset className="bg-[#dcebfe]">{children}</SidebarInset>
        </SidebarProvider>
      </body>
    </html>
  );
}
