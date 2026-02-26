"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navLinks = [
  { href: "/companies/greenworks", label: "Profil firmy", match: "/companies" },
  { href: "/tenders", label: "Przetargi", match: "/tenders", exact: true },
  { href: "/tenders/liked", label: "Polubione", match: "/tenders/liked" },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
      <div className="container mx-auto flex h-14 items-center gap-6 px-6">
        <Link href="/" className="font-semibold">
          Tenderec
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          {navLinks.map((link) => {
            const isActive = link.exact
              ? pathname === link.match
              : pathname.startsWith(link.match);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "transition-colors hover:text-foreground",
                  isActive
                    ? "text-foreground"
                    : "text-muted-foreground"
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
