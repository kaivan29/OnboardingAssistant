import Link from "next/link";
import { Button } from "@/components/ui/button";

export const Header = () => {
  return (
    <header className="flex h-14 w-full items-center justify-between border-b border-gray-200 px-6 lg:px-12 bg-white">
      <div className="flex items-center gap-3">
        {/* Logo Placeholder */}
        <div className="grid grid-cols-3 gap-1 w-6 h-6">
          {[...Array(9)].map((_, i) => (
            <div
              key={i}
              className={`w-1 h-1 rounded-full ${
                i % 2 === 0 ? "bg-black" : "bg-gray-400"
              }`}
            ></div>
          ))}
        </div>
        <span className="text-xl font-semibold tracking-tight text-black">
          Onboarding Assistant
        </span>
      </div>

      <Link href="/onboarding">
        <Button className="rounded-full px-6">Onboard with us!</Button>
      </Link>
    </header>
  );
};
