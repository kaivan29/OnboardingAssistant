'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Progress } from '@/components/ui/progress';
import { Brain, Code2, GitBranch } from 'lucide-react';
import { api, LearningPlan } from '@/lib/api';

export default function Dashboard() {
    const router = useRouter();
    const [plan, setPlan] = useState<LearningPlan | null>(null);
    const [loading, setLoading] = useState(true);
    const [candidateId, setCandidateId] = useState<number | null>(null);
    const [courseProgress] = useState(15); // Initial progress
    const [tasksDue] = useState(5); // Example tasks due
    const [loadingStatus, setLoadingStatus] = useState('Checking resume analysis...');

    useEffect(() => {
        const id = localStorage.getItem('candidateId');
        const codebaseUrl = localStorage.getItem('codebaseUrl');

        if (!id) {
            router.push('/');
            return;
        }

        const pollForPlan = async () => {
            try {
                const candidateIdNum = parseInt(id);
                setCandidateId(candidateIdNum);

                // Step 1: Wait for resume analysis to complete
                setLoadingStatus('Analyzing your resume with AI...');
                let analysisComplete = false;
                let attempts = 0;
                const maxAttempts = 60; // 2 minutes max

                while (!analysisComplete && attempts < maxAttempts) {
                    const status = await api.getCandidateStatus(candidateIdNum);

                    if (status.analysis_complete) {
                        analysisComplete = true;
                        console.log('Resume analysis complete!');
                    } else {
                        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
                        attempts++;
                    }
                }

                if (!analysisComplete) {
                    throw new Error('Resume analysis timed out');
                }

                // Step 2: Check if plan already exists
                setLoadingStatus('Generating your personalized study plan...');
                try {
                    const existingPlan = await api.getLearningPlan(candidateIdNum);
                    setPlan(existingPlan);
                    setLoading(false);
                    return;
                } catch (error) {
                    // Plan doesn't exist yet, generate it
                    console.log('No existing plan, generating new one...');
                }

                // Step 3: Generate learning plan
                const newPlan = await api.generateLearningPlan(
                    candidateIdNum,
                    codebaseUrl || 'https://github.com/facebook/rocksdb'
                );

                setPlan(newPlan);
                setLoading(false);
                setLoadingStatus('Complete!');
            } catch (error) {
                console.error('Error loading plan:', error);
                setLoadingStatus('Error: ' + (error as Error).message);
                setLoading(false);
            }
        };

        pollForPlan();
    }, [router]);

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-black mb-4"></div>
                <p className="text-gray-600 text-lg">{loadingStatus}</p>
            </div>
        );
    }

    if (!plan) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <p className="text-gray-600 mb-4">{loadingStatus}</p>
                    <button
                        onClick={() => router.push('/')}
                        className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800"
                    >
                        Go Back
                    </button>
                </div>
            </div>
        );
    }

    const userFirstName = "User"; // You can extract this from candidate data if available

    return (
        <div className="min-h-screen bg-gray-50">
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

                <button
                    onClick={() => router.push('/dashboard/profile')}
                    className="text-sm font-medium text-gray-600 hover:text-black transition-colors"
                >
                    View Profile
                </button>
            </header>

            {/* Main Content */}
            <main className="max-w-6xl mx-auto px-6 lg:px-12 py-12">
                {/* Welcome Section */}
                <div className="flex items-center gap-12 mb-16">
                    {/* Illustration */}
                    <div className="hidden lg:flex items-center justify-center w-64 h-48 relative">
                        <div className="absolute w-24 h-24 border-2 border-black rounded-xl transform -rotate-12 bg-white flex items-center justify-center">
                            <Code2 className="w-10 h-10 text-gray-800" />
                        </div>
                        <div className="absolute top-0 right-8 w-16 h-16 border-2 border-black rounded-lg transform rotate-12 bg-white flex items-center justify-center">
                            <GitBranch className="w-8 h-8 text-gray-800" />
                        </div>
                        <div className="absolute bottom-4 left-8 w-20 h-20 border-2 border-black rounded-full bg-white flex items-center justify-center">
                            <Brain className="w-10 h-10 text-gray-800" />
                        </div>
                    </div>

                    {/* Welcome Text */}
                    <div className="flex-1">
                        <h1 className="text-4xl font-semibold text-black mb-3">
                            Welcome back, {userFirstName}!
                        </h1>
                        <p className="text-gray-600 text-lg mb-6">
                            Continue your learning journey today. You have{" "}
                            <span className="font-semibold">{tasksDue} tasks due</span> this
                            week.
                        </p>

                        {/* Progress Bar */}
                        <div className="max-w-md">
                            <div className="flex items-center gap-2 mb-2">
                                <span className="text-sm font-medium text-gray-700">
                                    Course Progress:
                                </span>
                                <span className="text-sm text-gray-600">
                                    {courseProgress}% complete
                                </span>
                            </div>
                            <Progress value={courseProgress} className="h-3" />
                        </div>
                    </div>
                </div>

                {/* Weekly Modules Section */}
                <section>
                    <h2 className="text-2xl font-semibold text-black mb-6">
                        Your Weekly Modules
                    </h2>

                    {/* Show skeleton/disabled state while loading */}
                    {!plan ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                            {[1, 2, 3, 4].map((week) => (
                                <div
                                    key={week}
                                    className="bg-gray-100 border border-gray-200 rounded-xl p-6 opacity-50 cursor-not-allowed"
                                >
                                    <div className="flex items-center justify-between mb-4">
                                        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
                                            Week {week}
                                        </span>
                                        <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gray-200">
                                            <span className="text-sm font-bold text-gray-400">○</span>
                                        </div>
                                    </div>
                                    <h3 className="text-lg font-semibold text-gray-400 mb-3">
                                        Loading...
                                    </h3>
                                    <div className="space-y-2">
                                        <div className="text-xs text-gray-400">
                                            Generating content...
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                            {plan.weeks.map((week, index) => (
                                <button
                                    key={week.week_number}
                                    onClick={() => router.push(`/dashboard/week/${week.week_number}?candidateId=${candidateId}`)}
                                    className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-all text-left group"
                                >
                                    <div className="flex items-center justify-between mb-4">
                                        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                                            Week {week.week_number}
                                        </span>
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${index === 0 ? 'bg-blue-100' : 'bg-gray-100'
                                            }`}>
                                            <span className={`text-sm font-bold ${index === 0 ? 'text-blue-600' : 'text-gray-400'
                                                }`}>
                                                {index === 0 ? '→' : '○'}
                                            </span>
                                        </div>
                                    </div>

                                    <h3 className="text-lg font-semibold text-black mb-3 group-hover:text-blue-600 transition-colors">
                                        {week.title}
                                    </h3>

                                    <div className="space-y-2">
                                        <div className="text-xs text-gray-600">
                                            <span className="font-semibold">{week.objectives.length}</span> objectives
                                        </div>
                                        {week.topics && (
                                            <div className="text-xs text-gray-600">
                                                <span className="font-semibold">{week.topics.length}</span> topics
                                            </div>
                                        )}
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </section>
            </main>
        </div>
    );
}
