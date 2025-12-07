'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, ResumeAnalysis } from '@/lib/api';
import { User, Briefcase, Star, TrendingUp, ArrowRight, Award, BookOpen } from 'lucide-react';

export default function ProfilePage() {
    const router = useRouter();
    const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null);
    const [loading, setLoading] = useState(true);
    const [candidateName, setCandidateName] = useState('');

    useEffect(() => {
        const id = localStorage.getItem('candidateId');
        if (!id) {
            router.push('/');
            return;
        }

        const fetchAnalysis = async () => {
            try {
                const status = await api.getCandidateStatus(parseInt(id));
                if (status.resume_analysis) {
                    setAnalysis(status.resume_analysis);
                    setCandidateName(status.name);
                } else {
                    // If no analysis yet, redirect to dashboard to wait/poll
                    router.push('/dashboard');
                }
            } catch (error) {
                console.error('Error fetching profile:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchAnalysis();
    }, [router]);

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600 text-lg">Loading profile...</p>
                </div>
            </div>
        );
    }

    if (!analysis) {
        return null; // Will redirect in useEffect
    }

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="bg-white rounded-2xl shadow-sm p-8 mb-6 border border-gray-100">
                    <div className="flex items-center gap-6">
                        <div className="h-20 w-20 bg-blue-100 rounded-full flex items-center justify-center">
                            <User className="h-10 w-10 text-blue-600" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">{candidateName}</h1>
                            <p className="text-lg text-gray-600 mt-1 flex items-center gap-2">
                                <Award className="h-5 w-5 text-blue-500" />
                                {analysis.experience_level} Developer
                            </p>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Main Content Column */}
                    <div className="md:col-span-2 space-y-6">
                        {/* Background Summary */}
                        <div className="bg-white rounded-2xl shadow-sm p-8 border border-gray-100">
                            <div className="flex items-center gap-3 mb-4">
                                <Briefcase className="h-6 w-6 text-gray-700" />
                                <h2 className="text-xl font-bold text-gray-900">Background Summary</h2>
                            </div>
                            <p className="text-gray-700 leading-relaxed text-lg">
                                {analysis.background}
                            </p>
                        </div>

                        {/* Strengths */}
                        <div className="bg-white rounded-2xl shadow-sm p-8 border border-gray-100">
                            <div className="flex items-center gap-3 mb-6">
                                <Star className="h-6 w-6 text-yellow-500" />
                                <h2 className="text-xl font-bold text-gray-900">Key Strengths</h2>
                            </div>
                            <div className="grid gap-4">
                                {analysis.strengths.map((strength, idx) => (
                                    <div key={idx} className="flex items-start gap-4 p-4 bg-yellow-50 rounded-xl border border-yellow-100">
                                        <div className="h-6 w-6 rounded-full bg-yellow-200 text-yellow-700 flex items-center justify-center flex-shrink-0 text-sm font-bold">
                                            {idx + 1}
                                        </div>
                                        <p className="text-gray-800 font-medium">{strength}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Growth Areas */}
                        <div className="bg-white rounded-2xl shadow-sm p-8 border border-gray-100">
                            <div className="flex items-center gap-3 mb-6">
                                <TrendingUp className="h-6 w-6 text-green-500" />
                                <h2 className="text-xl font-bold text-gray-900">Areas for Growth</h2>
                            </div>
                            <ul className="space-y-4">
                                {analysis.learning_areas.map((area, idx) => (
                                    <li key={idx} className="flex items-start gap-3">
                                        <div className="mt-1.5 h-2 w-2 rounded-full bg-green-500 flex-shrink-0" />
                                        <span className="text-gray-700 text-lg">{area}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>

                    {/* Sidebar Column */}
                    <div className="space-y-6">
                        {/* Skills Matrix */}
                        <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
                            <div className="flex items-center gap-3 mb-6">
                                <BookOpen className="h-6 w-6 text-purple-600" />
                                <h2 className="text-xl font-bold text-gray-900">Skills Identified</h2>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {analysis.skills.map((skill, idx) => (
                                    <span
                                        key={idx}
                                        className="px-3 py-1.5 bg-purple-50 text-purple-700 rounded-lg text-sm font-medium border border-purple-100"
                                    >
                                        {skill}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Navigation Action */}
                        <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl shadow-lg p-6 text-white text-center">
                            <h3 className="text-xl font-bold mb-2">Ready to start?</h3>
                            <p className="text-blue-100 mb-6">Your personalized learning plan is ready.</p>
                            <button
                                onClick={() => router.push('/dashboard')}
                                className="w-full bg-white text-blue-600 font-bold py-3 px-6 rounded-xl hover:bg-blue-50 transition-colors flex items-center justify-center gap-2"
                            >
                                View Learning Plan
                                <ArrowRight className="h-5 w-5" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
