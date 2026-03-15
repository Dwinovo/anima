import type { Metadata } from "next";
import Image from "next/image";
import localFont from "next/font/local";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar";
import { AdminBreadcrumb } from "@/components/admin-breadcrumb";
import { AdminSidebarNav } from "@/components/admin-sidebar-nav";
import "./globals.css";

const notoSansSc = localFont({
  src: "./fonts/NotoSansCJKsc-VF.ttf",
  variable: "--font-noto-sans-sc",
  weight: "100 900",
  style: "normal",
  display: "swap",
});

const notoSerifSc = localFont({
  src: "./fonts/NotoSerifCJKsc-VF.ttf",
  variable: "--font-noto-serif-sc",
  weight: "200 900",
  style: "normal",
  display: "swap",
});

const geistMono = localFont({
  src: "./fonts/GeistMono-Variable.woff2",
  variable: "--font-geist-mono",
  weight: "100 900",
  style: "normal",
  display: "swap",
});

const archivoBlack = localFont({
  src: "./fonts/ArchivoBlack-Regular.ttf",
  variable: "--font-archivo-black",
  weight: "400",
  style: "normal",
  display: "swap",
});

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
      <body
        className={`${notoSansSc.variable} ${notoSerifSc.variable} ${geistMono.variable} ${archivoBlack.variable} font-base antialiased`}
      >
        <SidebarProvider className="bg-background">
          <Sidebar collapsible="icon">
            <SidebarHeader className="items-center justify-center p-4">
              <h1
                data-testid="sidebar-brandplate"
                className="inline-flex w-fit items-center justify-center gap-2 px-3 py-2 sm:px-4 sm:py-2.5"
              >
                <Image
                  src="/branding/logo.svg"
                  alt=""
                  width={28}
                  height={28}
                  aria-hidden
                  className="size-7"
                />
                <span className="logo-text-archivo" aria-label="Anima">
                  ANIMA
                </span>
              </h1>
            </SidebarHeader>
            <SidebarContent>
              <AdminSidebarNav />
            </SidebarContent>
          </Sidebar>
          <SidebarInset className="min-h-svh bg-panel-background px-6 py-8 font-base sm:px-8 lg:px-10">
            <div
              data-testid="page-layout"
              className="mx-auto flex w-full max-w-6xl flex-col gap-8"
            >
              <div
                data-testid="page-breadcrumb"
                className="flex w-full items-center justify-start"
              >
                <AdminBreadcrumb />
              </div>
              <div data-testid="content-surface" className="space-y-6">
                {children}
              </div>
            </div>
          </SidebarInset>
        </SidebarProvider>
      </body>
    </html>
  );
}
