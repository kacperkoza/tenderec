"use client";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
      <div className="container mx-auto flex h-14 items-center px-6">
        <div className="flex items-center gap-2 font-semibold">
          <span className="text-xl">📋</span>
          <span>Tenderec</span>
        </div>
        <div className="ml-auto text-sm text-muted-foreground">
          Tender Recommendation Engine
        </div>
      </div>
    </header>
  );
}

