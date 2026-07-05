"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";

export default function Nav() {
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path;

  return (
    <nav className="border-b border-border-hairline bg-background">
      <div className="px-4 sm:px-6 py-3 flex items-center justify-between gap-4 overflow-x-auto">
        <div className="flex items-center gap-4 sm:gap-8 shrink-0">
          <div className="shrink-0">
            <div className="font-semibold tracking-wide text-sm text-foreground whitespace-nowrap">
              POLARIS
            </div>
            <div className="text-xs text-muted-foreground whitespace-nowrap">
              Factoring Back Office
            </div>
          </div>
          <div className="flex items-center gap-4 sm:gap-6">
            <Link
              href="/cash-application"
              className={`text-[13px] font-medium whitespace-nowrap ${
                isActive("/cash-application")
                  ? "text-accent"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Cash Application
            </Link>
            <Link
              href="/collections"
              className={`text-[13px] font-medium whitespace-nowrap ${
                isActive("/collections")
                  ? "text-accent"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Collections
            </Link>
            <Link
              href="/portfolio"
              className={`text-[13px] font-medium whitespace-nowrap ${
                isActive("/portfolio")
                  ? "text-accent"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Portfolio
            </Link>
          </div>
        </div>
        <Button variant="outline" size="sm" className="shrink-0">
          Reset demo data
        </Button>
      </div>
    </nav>
  );
}
