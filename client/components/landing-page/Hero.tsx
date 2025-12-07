import { Button } from "@/components/ui/button";
import { ArrowUpRight, Brain, Code2, GitBranch, Terminal } from "lucide-react";
import Link from "next/link";

export function Hero() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[500px] border-b border-gray-200 divide-y lg:divide-y-0 lg:divide-x divide-gray-200 bg-white">
      {/* Left Content */}
      <div className="flex flex-col justify-center px-8 py-16 lg:px-16 lg:py-24">
        <h1 className="text-6xl font-medium tracking-tight text-black mb-6 leading-[1.1]">
          Digital Brain <br />
          for Codebase
        </h1>
        <p className="text-lg text-gray-600 mb-10 max-w-md leading-relaxed">
          We automate the most time-consuming workflows of onboarding every new
          hire. Onboarding Assistant understands your codebase so your team
          doesn't have to.
        </p>
        <div className="flex items-center gap-4">
          <Link href="/onboarding">
            <Button className="rounded-full group">
              Get Started
              <ArrowUpRight className="ml-2 h-6 w-6 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Right Illustration */}
      <div className="relative flex items-center justify-center p-12 bg-white overflow-hidden">
        {/* Isometric-style Illustration Placeholder */}
        <div className="relative w-full max-w-[500px] aspect-square">
          {/* Base Platform */}
          <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-[80%] h-[120px] bg-white border-2 border-black rounded-xl transform -skew-x-12 z-10 flex items-center justify-center shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
            <div className="flex gap-8 items-end pb-4">
              <Terminal className="w-10 h-10 text-gray-800 stroke-1" />
              <div className="w-32 h-20 border-2 border-black rounded-md bg-white -mb-8 relative z-20 flex items-center justify-center shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                <Code2 className="w-8 h-8 text-black" />
              </div>
            </div>
          </div>

          {/* Floating Elements */}
          <div className="absolute top-20 right-20 w-32 h-32 border-2 border-black bg-white rounded-lg transform rotate-12 z-0 flex flex-col items-center justify-center shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
            <div className="text-xs font-mono mb-2 border-b border-gray-200 w-full text-center pb-1">
              Repo
            </div>
            <GitBranch className="w-12 h-12 text-black stroke-1" />
          </div>

          <div className="absolute top-32 left-10 w-24 h-40 border-2 border-black bg-white rounded-full z-20 flex items-center justify-center shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
            <div className="flex flex-col items-center gap-2">
              <Brain className="w-10 h-10 text-black" />
              <span className="text-[10px] font-bold uppercase tracking-widest">
                Core
              </span>
            </div>
          </div>

          {/* Connecting Lines (Decorative) */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none z-0 opacity-20">
            <path
              d="M100,300 Q150,200 200,350"
              fill="none"
              stroke="black"
              strokeWidth="2"
              strokeDasharray="4 4"
            />
            <path
              d="M300,150 Q350,250 300,350"
              fill="none"
              stroke="black"
              strokeWidth="2"
              strokeDasharray="4 4"
            />
          </svg>
        </div>
      </div>
    </div>
  );
}
