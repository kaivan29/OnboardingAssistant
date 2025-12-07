'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Progress } from '@/components/ui/progress';
import { Brain, Code2, GitBranch, Check } from 'lucide-react';
import { api, LearningPlan } from '@/lib/api';
import CodebaseExplorer from '@/components/CodebaseExplorer';

export default function Dashboard() {
    const router = useRouter();
    const [plan, setPlan] = useState<LearningPlan | null>(null);
    const [loading, setLoading] = useState(true);
    const [candidateId, setCandidateId] = useState<number | null>(null);
    const [courseProgress, setCourseProgress] = useState(0);
    const [weekProgress, setWeekProgress] = useState<{ week_number: number; percent: number; is_complete: boolean }[]>([]);
    const [tasksDue] = useState(5); // Example tasks due
    const [loadingStatus, setLoadingStatus] = useState('Checking resume analysis...');
    const [activeTab, setActiveTab] = useState<'path' | 'codebase'>('path');
    const [candidateName, setCandidateName] = useState('User');

    useEffect(() => {
        if (candidateId) {
            api.getCourseProgress(candidateId).then(data => {
                setCourseProgress(data.progress);
                if (data.weeks_progress) {
                    setWeekProgress(data.weeks_progress);
                }
            }).catch(e => console.error("Failed to fetch progress", e));
        }
    }, [candidateId]);

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
                const maxAttempts = 300; // Increased timeout

                while (!analysisComplete && attempts < maxAttempts) {
                    const status = await api.getCandidateStatus(candidateIdNum);

                    if (status.name) {
                        setCandidateName(status.name.split(' ')[0]); // Use first name
                    }

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

    if (!plan && activeTab === 'path') {
        // Only show this if we are in path mode and failed to load plan, 
        // but actually we handled loading state above. 
        // If we are here, loading is false, but plan is null.
        // This implies error state.
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

                    <div className="flex-1">
                        <h1 className="text-4xl font-semibold text-black mb-3">
                            Welcome back, {candidateName}!
                        </h1>
                        <p className="text-gray-600 text-lg mb-6">
                            Continue your learning journey today. You have{" "}
                            <span className="font-semibold">{tasksDue} tasks due</span> this week.
                        </p>

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

                {/* Tabs */}
                <div className="flex items-center space-x-8 border-b border-gray-200 mb-8">
                    <button
                        onClick={() => setActiveTab('path')}
                        className={`pb-3 text-sm font-medium transition-all border-b-2 ${activeTab === 'path'
                            ? 'border-black text-black'
                            : 'border-transparent text-gray-500 hover:text-gray-800'
                            }`}
                    >
                        Learning Path
                    </button>
                    <button
                        onClick={() => setActiveTab('codebase')}
                        className={`pb-3 text-sm font-medium transition-all border-b-2 ${activeTab === 'codebase'
                            ? 'border-black text-black'
                            : 'border-transparent text-gray-500 hover:text-gray-800'
                            }`}
                        title="Browse the RocksDB codebase"
                    >
                        Codebase Browser
                    </button>
                </div>

                {activeTab === 'path' ? (
                    <section>
                        <h2 className="text-2xl font-semibold text-black mb-6">
                            Your Weekly Modules
                        </h2>
                        {!plan ? (
                            <div className="text-center text-gray-500 py-12">
                                Failed to load plan. Please try refreshing.
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                                {plan.weeks.map((week) => {
                                    const progressData = weekProgress.find(wp => wp.week_number === week.week_number);
                                    const isComplete = progressData?.is_complete;

                                    // Determine if this is the active week (first incomplete week)
                                    let isActive = false;
                                    if (weekProgress.length > 0) {
                                        const sortedProgress = [...weekProgress].sort((a, b) => a.week_number - b.week_number);
                                        const firstIncomplete = sortedProgress.find(w => !w.is_complete);
                                        isActive = firstIncomplete ? week.week_number === firstIncomplete.week_number : false;
                                    } else {
                                        isActive = week.week_number === 1;
                                    }

                                    return (
                                        <button
                                            key={week.week_number}
                                            onClick={() => router.push(`/dashboard/week/${week.week_number}?candidateId=${candidateId}`)}
                                            className={`border rounded-xl p-6 hover:shadow-lg transition-all text-left group relative overflow-hidden ${isComplete ? 'bg-green-50 border-green-200' :
                                                isActive ? 'bg-white border-blue-200 ring-2 ring-blue-50' :
                                                    'bg-white border-gray-200'
                                                }`}
                                        >
                                            <div className="flex items-center justify-between mb-4">
                                                <span className={`text-xs font-semibold uppercase tracking-wide ${isActive ? 'text-blue-600' : 'text-gray-500'
                                                    }`}>
                                                    Week {week.week_number}
                                                </span>
                                                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${isComplete ? 'bg-green-100' :
                                                    isActive ? 'bg-blue-100' : 'bg-gray-100'
                                                    }`}>
                                                    {isComplete ? (
                                                        <Check className="w-5 h-5 text-green-600" />
                                                    ) : (
                                                        <span className={`text-sm font-bold ${isActive ? 'text-blue-600' : 'text-gray-400'
                                                            }`}>
                                                            {isActive ? '→' : '○'}
                                                        </span>
                                                    )}
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

                                            {progressData && (
                                                <div className="mt-4">
                                                    <div className="flex justify-between items-center mb-1">
                                                        <span className="text-[10px] font-medium text-gray-500">Progress</span>
                                                        <span className={`text-[10px] font-bold ${isComplete ? 'text-green-600' : isActive ? 'text-blue-600' : 'text-gray-500'}`}>
                                                            {progressData.percent}%
                                                        </span>
                                                    </div>
                                                    <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                                                        <div
                                                            className={`h-1.5 rounded-full transition-all duration-500 ${isComplete ? 'bg-green-500' : isActive ? 'bg-blue-500' : 'bg-gray-300'
                                                                }`}
                                                            style={{ width: `${progressData.percent}%` }}
                                                        ></div>
                                                    </div>
                                                </div>
                                            )}
                                        </button>
                                    );
                                })}
                            </div>
                        )}
                    </section>
                ) : (
                    <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <CodebaseExplorer codebaseId="rocksdb" />
                    </div>
                )}
            </main>
        </div>
    );
}
