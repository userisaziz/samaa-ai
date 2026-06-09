"use client";

import { AuthGuard } from "@/components/auth-guard";
import { Sidebar } from "@/components/layout/sidebar";
import { MobileSidebar } from "@/components/layout/mobile-sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <div className="flex h-screen overflow-hidden">
        {/* Desktop sidebar (lg+) */}
        <aside className="hidden lg:flex lg:shrink-0 lg:h-full">
          <Sidebar />
        </aside>

        {/* Mobile sidebar drawer (< lg) */}
        <MobileSidebar>
          <Sidebar />
        </MobileSidebar>

        <main className="flex-1 overflow-y-auto bg-surface-soft">
          {children}
        </main>
      </div>
    </AuthGuard>
  );
}
