import React from "react";

export function PageLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="w-full min-h-screen bg-white font-sans">
      {children}
    </div>
  );
}
