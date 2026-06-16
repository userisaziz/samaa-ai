"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTitle,
} from "@/components/ui/sheet";

interface MobileSidebarProps {
  children: React.ReactNode;
  /** Breakpoint class prefix where sidebar becomes permanent (default: "lg") */
  breakpoint?: "md" | "lg" | "xl";
}

/**
 * Wraps a sidebar component for mobile: shows a hamburger toggle on small screens
 * that opens the sidebar in a slide-out drawer. Auto-closes on navigation.
 * On larger screens, renders nothing (the sidebar is shown permanently via layout).
 */
export function MobileSidebar({ children, breakpoint = "lg" }: MobileSidebarProps) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  // Close drawer on navigation
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  const hideClass = breakpoint === "md" ? "md:hidden" : breakpoint === "xl" ? "xl:hidden" : "lg:hidden";

  return (
    <div className={hideClass}>
      {/* Mobile top bar */}
      <div className="sticky top-0 z-40 flex h-14 items-center gap-3 border-b border-border bg-card/95 backdrop-blur-sm px-4">
        <Button
          variant="ghost"
          size="icon"
          className="h-10 w-10 shrink-0"
          onClick={() => setOpen(true)}
          aria-label="Open navigation menu"
        >
          <Menu className="h-5 w-5" />
        </Button>
        <span className="text-sm font-semibold tracking-tight text-ink">CXSAMAA</span>
      </div>

      {/* Slide-out drawer */}
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="left" className="w-64 p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          {children}
        </SheetContent>
      </Sheet>
    </div>
  );
}
