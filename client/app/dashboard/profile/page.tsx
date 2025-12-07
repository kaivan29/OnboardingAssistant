"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ResumeAnalysis } from "@/lib/api";
import {
  User,
  Briefcase,
  Star,
  TrendingUp,
  ArrowRight,
  Award,
  BookOpen,
} from "lucide-react";

export default function ProfilePage() {
  const router = useRouter();
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [candidateName, setCandidateName] = useState("");

  useEffect(() => {
    const id = localStorage.getItem("candidateId");
    if (!id) {
      router.push("/");
      return;
    }

    const pollForAnalysis = async () => {
      try {
        const candidateIdNum = parseInt(id);
        // Poll for analysis completion
        let analysisComplete = false;
        let attempts = 0;
        const maxAttempts = 60; // 2 minutes max

        while (!analysisComplete && attempts < maxAttempts) {
          const status = await api.getCandidateStatus(candidateIdNum);

          if (status.analysis_complete && status.resume_analysis) {
            setAnalysis(status.resume_analysis);
            setCandidateName(status.name);
            analysisComplete = true;
          } else {
            attempts++;
            await new Promise((resolve) => setTimeout(resolve, 2000)); // Wait 2 seconds
          }
        }

        if (!analysisComplete) {
          // Handle timeout - maybe show an error or redirect
          console.error("Analysis timed out");
          // Optional: set an error state here
        }
      } catch (error) {
        console.error("Error fetching profile:", error);
      } finally {
        setLoading(false);
      }
    };

    pollForAnalysis();
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-black mb-4"></div>
        <p className="text-gray-600 text-lg">
          Analyzing your resume with AI...
        </p>
      </div>
    );
  }

  if (!analysis) {
    return null; // Will redirect in useEffect
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="flex h-14 w-full items-center justify-between border-b border-gray-200 px-6 lg:px-12 bg-white">
        <div className="flex items-center gap-3">
          <div className="grid grid-cols-3 gap-1 w-6 h-6">
            {[...Array(9)].map((_, i) => (
              <div
                key={i}
                className={`w-1 h-1 rounded-full ${
                  i % 2 === 0 ? "bg-black" : "bg-gray-400"
                }`}
              />
            ))}
          </div>
          <span className="text-xl font-semibold tracking-tight text-black">
            Onboarding Assistant
          </span>
        </div>

        <button
          onClick={() => router.push("/dashboard")}
          className="text-sm font-medium text-gray-600 hover:text-black transition-colors"
        >
          Back to Dashboard
        </button>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 lg:px-12 py-12">
        {/* Profile Header */}
        <div className="bg-white rounded-xl border border-gray-200 p-8 mb-8">
          <div className="flex items-center gap-6">
            <div className="h-20 w-20 bg-gray-100 rounded-full flex items-center justify-center border-2 border-gray-200">
              <User className="h-10 w-10 text-gray-800" />
            </div>
            <div>
              <h1 className="text-4xl font-semibold text-black mb-2">
                {candidateName}
              </h1>
              <p className="text-lg text-gray-600 flex items-center gap-2">
                <Award className="h-5 w-5 text-gray-600" />
                {analysis.experience_level} Developer
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Ramp Up Expectation */}
            {analysis.ramp_up_expectation && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <TrendingUp className="h-5 w-5 text-black" />
                  <h2 className="text-xl font-semibold text-black">
                    Ramp Up Expectation
                  </h2>
                </div>
                <p className="text-gray-700 leading-relaxed text-base italic">
                  "{analysis.ramp_up_expectation}"
                </p>
              </div>
            )}

            {/* Background Summary */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <Briefcase className="h-5 w-5 text-black" />
                <h2 className="text-xl font-semibold text-black">
                  Background Summary
                </h2>
              </div>
              <p className="text-gray-700 leading-relaxed text-base">
                {analysis.background}
              </p>
            </div>

            {/* Strengths */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-6">
                <Star className="h-5 w-5 text-black" />
                <h2 className="text-xl font-semibold text-black">
                  Key Strengths
                </h2>
              </div>
              <div className="grid gap-3">
                {analysis.strengths.map((strength, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="h-6 w-6 rounded-full bg-black text-white flex items-center justify-center shrink-0 text-xs font-semibold">
                      {idx + 1}
                    </div>
                    <p className="text-gray-800 font-medium text-sm">
                      {strength}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Growth Areas */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-6">
                <TrendingUp className="h-5 w-5 text-black" />
                <h2 className="text-xl font-semibold text-black">
                  Areas for Growth
                </h2>
              </div>
              <ul className="space-y-3">
                {analysis.learning_areas.map((area, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <div className="mt-1.5 h-2 w-2 rounded-full bg-black shrink-0" />
                    <span className="text-gray-700 text-sm">{area}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Sidebar Column */}
          <div className="space-y-6">
            {/* Skills Matrix */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-6">
                <BookOpen className="h-5 w-5 text-black" />
                <h2 className="text-xl font-semibold text-black">
                  Skills Identified
                </h2>
              </div>
              <div className="flex flex-wrap gap-2">
                {analysis.skills.map((skill, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 bg-gray-50 text-gray-800 rounded-lg text-sm font-medium border border-gray-200"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* Navigation Action */}
            <div className="bg-black rounded-xl border border-gray-200 p-6 text-white">
              <h3 className="text-lg font-semibold mb-2">Ready to start?</h3>
              <p className="text-gray-300 mb-6 text-sm">
                Your personalized learning plan is ready.
              </p>
              <button
                onClick={() => router.push("/dashboard")}
                className="w-full bg-white text-black font-semibold py-3 px-6 rounded-lg hover:bg-gray-100 transition-colors flex items-center justify-center gap-2 text-sm"
              >
                View Learning Plan
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
