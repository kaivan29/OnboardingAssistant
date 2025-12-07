'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { FileUpload } from '@/components/ui/file-upload';
import { MultiStepLoader } from '@/components/ui/multi-step-loader';
import { IconSquareRoundedX } from '@tabler/icons-react';
import { CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { api, Candidate, LearningPlan } from '@/lib/api';
import { toast } from 'sonner';

const loadingStates = [
  { text: 'Uploading resume...' },
  { text: 'Analyzing your experience with AI' },
  { text: 'Identifying technical skills and gaps' },
  { text: 'Analyzing codebase structure' },
  { text: 'Generating personalized learning path' },
  { text: 'Creating weekly tasks and chapters' },
  { text: 'Finalizing your custom study plan' },
];

interface AnalysisResult {
  candidate: Candidate;
  plan: LearningPlan;
}

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  const handleFileUpload = useCallback(async (uploadedFiles: File[]) => {
    if (uploadedFiles.length === 0) return;

    setLoading(true);

    try {
      // Upload resume - returns immediately
      const candidate = await api.uploadResume(
        uploadedFiles[0],
        'New Candidate',
        'candidate@example.com'
      );
      console.log('Candidate created:', candidate);

      // Store candidate ID for dashboard
      localStorage.setItem('candidateId', candidate.id.toString());
      localStorage.setItem('codebaseUrl', 'https://github.com/facebook/rocksdb');

      toast.success('Resume uploaded! Generating your personalized plan...');

      // Navigate immediately to dashboard - it will handle polling for analysis/plan
      router.push('/dashboard');
    } catch (error: any) {
      console.error('Upload failed:', error);

      // Show more detailed error message
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to upload resume';
      toast.error(`Error: ${errorMessage}. Please ensure the backend is running on port 8000.`);

      setLoading(false);
    }
  }, [router]);

  const handleConfirm = useCallback(() => {
    if (analysisResult) {
      // Store candidate ID for dashboard
      localStorage.setItem('candidateId', analysisResult.candidate.id.toString());
    }

    toast.success("Let's start your personalized onboarding!");
    // Redirect to profile page first to see analysis
    router.push('/dashboard/profile');
  }, [analysisResult, router]);

  const handleClose = useCallback(() => {
    setLoading(false);
  }, []);

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="flex h-14 w-full items-center justify-between border-b border-gray-200 px-6 lg:px-12 bg-white">
        <div className="flex items-center gap-3">
          <div className="grid grid-cols-3 gap-1 w-6 h-6">
            {[...Array(9)].map((_, i) => (
              <div
                key={i}
                className={`w-1 h-1 rounded-full ${i % 2 === 0 ? 'bg-black' : 'bg-gray-400'}`}
              />
            ))}
          </div>
          <span className="text-xl font-semibold tracking-tight text-black">
            Onboarding Assistant
          </span>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-col items-center justify-center px-6 py-16 lg:py-24">
        {!showConfirmation ? (
          <>
            <div className="max-w-2xl w-full text-center mb-12">
              <h1 className="text-4xl lg:text-5xl font-medium tracking-tight text-black mb-4">
                Upload Your Resume
              </h1>
              <p className="text-lg text-gray-600 leading-relaxed">
                We'll analyze your experience with AI and generate a personalized
                study plan tailored to your background and knowledge gaps.
              </p>
            </div>

            {/* File Upload */}
            <div className="w-full max-w-2xl border border-dashed border-gray-200 rounded-lg bg-gray-50/50">
              <FileUpload onChange={handleFileUpload} />
            </div>
          </>
        ) : (
          // Confirmation Screen
          <div className="max-w-4xl w-full">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
              </div>
              <h1 className="text-3xl lg:text-4xl font-medium tracking-tight text-black mb-2">
                Your Personalized Plan is Ready!
              </h1>
              <p className="text-lg text-gray-600">
                Review your analysis and customized learning path below
              </p>
            </div>

            {analysisResult && (
              <div className="space-y-6">
                {/* Profile Analysis */}
                <Card>
                  <CardHeader>
                    <CardTitle>Profile Analysis</CardTitle>
                    <CardDescription>
                      AI-powered analysis of your resume
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h3 className="font-semibold text-sm text-gray-700 mb-2">Candidate</h3>
                      <p className="text-lg">{analysisResult.candidate.name}</p>
                      {analysisResult.candidate.resume_analysis && (
                        <p className="text-sm text-gray-600">
                          {analysisResult.candidate.resume_analysis.experience_level}
                        </p>
                      )}
                    </div>

                    {analysisResult.candidate.resume_analysis?.skills && (
                      <div>
                        <h3 className="font-semibold text-sm text-gray-700 mb-2">Technical Skills</h3>
                        <div className="flex flex-wrap gap-2">
                          {analysisResult.candidate.resume_analysis.skills.slice(0, 8).map((skill) => (
                            <span key={skill} className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {analysisResult.candidate.resume_analysis?.learning_areas &&
                      analysisResult.candidate.resume_analysis.learning_areas.length > 0 && (
                        <div>
                          <h3 className="font-semibold text-sm text-gray-700 mb-2">Areas to Focus On</h3>
                          <ul className="space-y-1">
                            {analysisResult.candidate.resume_analysis.learning_areas.slice(0, 3).map((area, idx) => (
                              <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                                <span className="text-orange-500 mt-1">→</span>
                                {area}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                  </CardContent>
                </Card>

                {/* Study Plan Summary */}
                <Card>
                  <CardHeader>
                    <CardTitle>Your Customized Study Plan</CardTitle>
                    <CardDescription>
                      4-week personalized onboarding path
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {analysisResult.plan.weeks.map((week) => (
                        <div key={week.week_number} className="p-4 border rounded-lg">
                          <div className="text-sm font-semibold text-gray-700 mb-1">
                            Week {week.week_number}
                          </div>
                          <div className="text-xs text-gray-600 mb-2">{week.title}</div>
                          <div className="flex items-center gap-2 text-xs">
                            <span className="text-gray-500">{week.objectives.length} objectives</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Action Buttons */}
                <div className="flex justify-center gap-4 pt-6">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowConfirmation(false);
                      setAnalysisResult(null);
                    }}
                  >
                    Upload Different Resume
                  </Button>
                  <Button
                    onClick={handleConfirm}
                    className="bg-black hover:bg-gray-800 text-white px-8"
                  >
                    Start My Onboarding Journey
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Multi-Step Loader */}
      <MultiStepLoader
        loadingStates={loadingStates}
        loading={loading}
        duration={2000}
        loop={false}
      />

      {/* Close Button */}
      {loading && (
        <button
          className="fixed top-4 right-4 text-black dark:text-white z-[120]"
          onClick={handleClose}
        >
          <IconSquareRoundedX className="h-10 w-10" />
        </button>
      )}
    </div>
  );
}
