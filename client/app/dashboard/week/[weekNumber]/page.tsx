'use client';

import { useEffect, useState } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { api, WeeklyContent } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

type Tab = 'reading' | 'tasks' | 'quiz';

const ReasonBadge = ({ reason }: { reason?: string }) => {
    if (!reason) return null;
    return (
        <div className="group relative inline-block ml-2 align-middle">
            <span className="cursor-help inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 text-sm font-bold border border-indigo-200 hover:bg-indigo-200 transition-colors">
                ?
            </span>
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">
                <div className="font-semibold mb-1 text-xs uppercase text-indigo-300">Why this matters</div>
                {reason}
                <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
            </div>
        </div>
    );
};

export default function WeekPage() {
    const params = useParams();
    const searchParams = useSearchParams();
    const router = useRouter();
    const weekNumber = parseInt(params.weekNumber as string);
    const candidateId = searchParams.get('candidateId');

    const [content, setContent] = useState<WeeklyContent | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<Tab>('reading');
    const [quizAnswers, setQuizAnswers] = useState<{ [key: string]: number }>({});
    const [quizSubmitted, setQuizSubmitted] = useState(false);
    const [completedTasks, setCompletedTasks] = useState<Set<string>>(new Set());

    // Chapter navigation state
    const [currentChapter, setCurrentChapter] = useState(0);
    const [completedChapters, setCompletedChapters] = useState<number[]>([]);
    const [chapters, setChapters] = useState<{ title: string; content: string }[]>([]);

    // Split reading material into chapters - combine multiple H2 sections for longer chapters (~1000 words)
    useEffect(() => {
        if (content?.reading_material?.content) {
            const splitChapters = [];
            const lines = content.reading_material.content.split('\n');
            let currentTitle = '';
            let currentContent = '';
            let sectionCount = 0;
            const SECTIONS_PER_CHAPTER = 2; // Combine 2 H2 sections per chapter for longer content

            for (const line of lines) {
                if (line.startsWith('## ')) {
                    sectionCount++;

                    // Start a new chapter every N sections
                    if (sectionCount > SECTIONS_PER_CHAPTER && currentTitle) {
                        splitChapters.push({ title: currentTitle, content: currentContent.trim() });
                        currentTitle = line.replace('## ', '');
                        currentContent = '';
                        sectionCount = 1;
                    } else {
                        // First section or continuing current chapter
                        if (!currentTitle) {
                            currentTitle = line.replace('## ', '');
                        }
                        currentContent += '\n### ' + line.replace('## ', '') + '\n';
                    }
                } else {
                    currentContent += line + '\n';
                }
            }

            // Add last chapter
            if (currentTitle || currentContent) {
                splitChapters.push({ title: currentTitle, content: currentContent.trim() });
            }

            setChapters(splitChapters.length > 0 ? splitChapters : [{ title: content.reading_material.title, content: content.reading_material.content }]);
        }
    }, [content]);

    // Fetch week progress for completed chapters
    useEffect(() => {
        if (!candidateId) return;

        const fetchProgress = async () => {
            try {
                const progress = await api.getWeekProgress(parseInt(candidateId), weekNumber);
                setCompletedChapters(progress.completed_chapters);
            } catch (error) {
                console.error('Error fetching progress:', error);
            }
        };

        fetchProgress();
    }, [candidateId, weekNumber]);

    useEffect(() => {
        if (!candidateId) {
            router.push('/dashboard');
            return;
        }

        const fetchContent = async () => {
            try {
                const weekContent = await api.getWeeklyContent(parseInt(candidateId), weekNumber);
                setContent(weekContent);
            } catch (error) {
                console.error('Error fetching weekly content:', error);
                alert('Failed to load weekly content');
            } finally {
                setLoading(false);
            }
        };

        fetchContent();
    }, [weekNumber, candidateId, router]);

    const handleTaskComplete = async (taskId: string) => {
        if (!candidateId) return;

        try {
            await api.updateProgress(parseInt(candidateId), weekNumber, { task_id: taskId });
            setCompletedTasks(prev => new Set([...prev, taskId]));
        } catch (error) {
            console.error('Error updating progress:', error);
        }
    };

    const handleQuizSubmit = async () => {
        if (!candidateId || !content) return;

        const answerArray = content.quiz.map(q => quizAnswers[q.id] ?? -1);

        try {
            await api.updateProgress(parseInt(candidateId), weekNumber, {
                quiz_answers: answerArray
            });
            setQuizSubmitted(true);
        } catch (error) {
            console.error('Error submitting quiz:', error);
        }
    };

    const calculateQuizScore = () => {
        if (!content) return 0;
        let correct = 0;
        content.quiz.forEach(q => {
            if (quizAnswers[q.id] === q.correct_answer) {
                correct++;
            }
        });
        return Math.round((correct / content.quiz.length) * 100);
    };

    const handleMarkChapterComplete = async () => {
        if (!candidateId) return;

        try {
            const result = await api.markChapterComplete(parseInt(candidateId), weekNumber, currentChapter);
            setCompletedChapters(result.completed_chapters);

            // Auto-advance to next chapter if available
            if (currentChapter < chapters.length - 1) {
                setCurrentChapter(currentChapter + 1);
            }
        } catch (error) {
            console.error('Error marking chapter complete:', error);
        }
    };

    const isChapterCompleted = (chapterIndex: number) => {
        return completedChapters.includes(chapterIndex);
    };

    const canNavigateToChapter = (chapterIndex: number) => {
        // Can always navigate to current or any previous chapter
        if (chapterIndex <= currentChapter) return true;
        // Can go to next if current is completed
        if (chapterIndex === currentChapter + 1) return isChapterCompleted(currentChapter);
        return false;
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600 text-lg">Loading weekly content...</p>
                </div>
            </div>
        );
    }

    if (!content) {
        return (
            <div className="max-w-7xl mx-auto px-4 py-12">
                <p className="text-center text-gray-600">No content found for this week</p>
            </div>
        );
    }

    // Check if individual content sections are ready
    const hasReading = content.reading_material && content.reading_material.content;
    const hasTasks = content.coding_tasks && content.coding_tasks.length > 0;
    const hasQuiz = content.quiz && content.quiz.length > 0;

    return (
        <div className="max-w-7xl mx-auto px-4 py-12">
            {/* Header */}
            <div className="mb-8">
                <button
                    onClick={() => router.push('/dashboard')}
                    className="text-blue-600 hover:text-blue-800 mb-4 flex items-center gap-2"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Back to Dashboard
                </button>

                <h1 className="text-4xl font-bold text-gray-900 mb-2">
                    Week {weekNumber}: {hasReading ? content.reading_material.title : 'Loading...'}
                    {hasReading && <ReasonBadge reason={content.reading_material.reason} />}
                </h1>
            </div>

            {/* Tabs */}
            <div className="bg-white rounded-xl shadow-lg mb-6">
                <div className="border-b border-gray-200">
                    <div className="flex">
                        <button
                            onClick={() => hasReading && setActiveTab('reading')}
                            disabled={!hasReading}
                            className={`px-6 py-4 font-semibold transition-colors ${!hasReading
                                ? 'text-gray-400 cursor-not-allowed opacity-50'
                                : activeTab === 'reading'
                                    ? 'border-b-2 border-blue-600 text-blue-600'
                                    : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            📚 Reading Material {!hasReading && '(Generating...)'}
                        </button>
                        <button
                            onClick={() => hasTasks && setActiveTab('tasks')}
                            disabled={!hasTasks}
                            className={`px-6 py-4 font-semibold transition-colors ${!hasTasks
                                ? 'text-gray-400 cursor-not-allowed opacity-50'
                                : activeTab === 'tasks'
                                    ? 'border-b-2 border-blue-600 text-blue-600'
                                    : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            💻 Coding Tasks {!hasTasks && '(Generating...)'}
                        </button>
                        <button
                            onClick={() => hasQuiz && setActiveTab('quiz')}
                            disabled={!hasQuiz}
                            className={`px-6 py-4 font-semibold transition-colors ${!hasQuiz
                                ? 'text-gray-400 cursor-not-allowed opacity-50'
                                : activeTab === 'quiz'
                                    ? 'border-b-2 border-blue-600 text-blue-600'
                                    : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            📝 Quiz {!hasQuiz && '(Generating...)'}
                        </button>
                    </div>
                </div>

                <div className="p-8">
                    {/* Reading Tab */}
                    {activeTab === 'reading' && (
                        hasReading ? (
                            <div className="max-w-none">
                                {/* Chapter Progress Indicator */}
                                <div className="mb-6 flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <h3 className="text-lg font-semibold text-gray-700">
                                            Part {currentChapter + 1} of {chapters.length}
                                        </h3>
                                        {isChapterCompleted(currentChapter) && (
                                            <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                                                ✓ Completed
                                            </span>
                                        )}
                                    </div>

                                    {/* Chapter Navigation Dots */}
                                    <div className="flex gap-2">
                                        {chapters.map((_, idx) => (
                                            <button
                                                key={idx}
                                                onClick={() => canNavigateToChapter(idx) && setCurrentChapter(idx)}
                                                disabled={!canNavigateToChapter(idx)}
                                                className={`w-3 h-3 rounded-full transition-colors ${idx === currentChapter
                                                    ? 'bg-blue-600'
                                                    : isChapterCompleted(idx)
                                                        ? 'bg-green-500'
                                                        : canNavigateToChapter(idx)
                                                            ? 'bg-gray-300 hover:bg-gray-400'
                                                            : 'bg-gray-200 cursor-not-allowed'
                                                    }`}
                                                title={`Part ${idx + 1}${isChapterCompleted(idx) ? ' (Completed)' : ''}`}
                                            />
                                        ))}
                                    </div>
                                </div>

                                {/* Current Chapter Content */}
                                <div className="mb-6">
                                    <h2 className="text-3xl font-bold text-gray-900 mb-6">
                                        {chapters[currentChapter]?.title || 'Loading...'}
                                    </h2>

                                    <div className="bg-gray-50 rounded-lg p-6">
                                        <div className="prose prose-slate max-w-none">
                                            <ReactMarkdown
                                                components={{
                                                    h1: ({ node, ...props }) => <h1 className="text-2xl font-bold mb-4 mt-6" {...props} />,
                                                    h2: ({ node, ...props }) => <h2 className="text-xl font-bold mb-3 mt-5" {...props} />,
                                                    h3: ({ node, ...props }) => <h3 className="text-lg font-semibold mb-2 mt-4" {...props} />,
                                                    p: ({ node, ...props }) => <p className="mb-3 text-gray-700 leading-relaxed" {...props} />,
                                                    code: ({ node, className, children, ...props }) => {
                                                        const match = /language-(\w+)/.exec(className || '');
                                                        const language = match ? match[1] : 'cpp';
                                                        const isInline = !match;

                                                        return isInline ? (
                                                            <code className="bg-gray-200 px-1.5 py-0.5 rounded text-sm font-mono text-red-600" {...props}>
                                                                {children}
                                                            </code>
                                                        ) : (
                                                            <SyntaxHighlighter
                                                                style={vscDarkPlus}
                                                                language={language}
                                                                PreTag="div"
                                                                className="rounded-lg my-3"
                                                                customStyle={{
                                                                    padding: '1rem',
                                                                    fontSize: '0.875rem',
                                                                    lineHeight: '1.5',
                                                                }}
                                                            >
                                                                {String(children).replace(/\n$/, '')}
                                                            </SyntaxHighlighter>
                                                        );
                                                    },
                                                    pre: ({ node, ...props }) => <pre {...props} />,
                                                    ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-3 space-y-1" {...props} />,
                                                    ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-3 space-y-1" {...props} />,
                                                    li: ({ node, ...props }) => <li className="text-gray-700 ml-4" {...props} />,
                                                    a: ({ node, ...props }) => <a className="text-blue-600 hover:underline" {...props} />,
                                                    blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-gray-300 pl-4 italic my-3" {...props} />,
                                                }}
                                            >
                                                {chapters[currentChapter]?.content || ''}
                                            </ReactMarkdown>
                                        </div>
                                    </div>
                                </div>

                                {/* Chapter Navigation Buttons */}
                                <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
                                    <button
                                        onClick={() => setCurrentChapter(currentChapter - 1)}
                                        disabled={currentChapter === 0}
                                        className="px-6 py-3 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
                                    >
                                        ← Previous Part
                                    </button>

                                    <div className="flex gap-3">
                                        {!isChapterCompleted(currentChapter) && (
                                            <button
                                                onClick={handleMarkChapterComplete}
                                                className="px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition"
                                            >
                                                ✓ Mark as Complete
                                            </button>
                                        )}

                                        <button
                                            onClick={() => setCurrentChapter(currentChapter + 1)}
                                            disabled={currentChapter === chapters.length - 1 || !isChapterCompleted(currentChapter)}
                                            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
                                        >
                                            Next Part →
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mx-auto mb-4"></div>
                                <p className="text-gray-600 text-lg">Generating reading material...</p>
                                <p className="text-gray-500 text-sm mt-2">This usually takes 1-2 minutes</p>
                            </div>
                        )
                    )}

                    {/* Tasks Tab */}
                    {activeTab === 'tasks' && (
                        hasTasks ? (
                            <div className="space-y-6">{content.coding_tasks.map((task) => (
                                <div key={task.id} className="border border-gray-200 rounded-lg p-6 hover:border-blue-500 transition">
                                    <div className="flex items-start justify-between mb-4">
                                        <div>
                                            <h3 className="text-xl font-bold text-gray-900 mb-2">
                                                {task.title}
                                                <ReasonBadge reason={task.reason} />
                                            </h3>
                                            <div className="flex gap-4 text-sm text-gray-600">
                                                <span className={`px-3 py-1 rounded-full ${task.difficulty === 'easy' ? 'bg-green-100 text-green-800' :
                                                    task.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                                        'bg-red-100 text-red-800'
                                                    }`}>
                                                    {task.difficulty}
                                                </span>
                                                <span>⏱️ {task.estimated_time}</span>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => handleTaskComplete(task.id)}
                                            disabled={completedTasks.has(task.id)}
                                            className={`px-4 py-2 rounded-lg font-semibold transition ${completedTasks.has(task.id)
                                                ? 'bg-green-100 text-green-800'
                                                : 'bg-blue-600 text-white hover:bg-blue-700'
                                                }`}
                                        >
                                            {completedTasks.has(task.id) ? '✓ Completed' : 'Mark Complete'}
                                        </button>
                                    </div>

                                    <p className="text-gray-700 mb-4">{task.description}</p>

                                    <div className="mb-4">
                                        <p className="font-semibold text-gray-900 mb-2">Files to modify:</p>
                                        <div className="flex flex-wrap gap-2">
                                            {task.files_to_modify.map((file, idx) => (
                                                <code key={idx} className="bg-gray-100 px-3 py-1 rounded text-sm">
                                                    {file}
                                                </code>
                                            ))}
                                        </div>
                                    </div>

                                    {task.hints.length > 0 && (
                                        <details className="mt-4">
                                            <summary className="cursor-pointer font-semibold text-blue-600 hover:text-blue-800">
                                                💡 Show Hints
                                            </summary>
                                            <ul className="mt-2 space-y-1 list-disc list-inside text-gray-600">
                                                {task.hints.map((hint, idx) => (
                                                    <li key={idx}>{hint}</li>
                                                ))}
                                            </ul>
                                        </details>
                                    )}
                                </div>
                            ))}
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mx-auto mb-4"></div>
                                <p className="text-gray-600 text-lg">Generating coding tasks...</p>
                                <p className="text-gray-500 text-sm mt-2">This usually takes 1-2 minutes</p>
                            </div>
                        )
                    )}

                    {/* Quiz Tab */}
                    {activeTab === 'quiz' && (
                        hasQuiz ? (
                            <div className="max-w-3xl">
                                {!quizSubmitted ? (
                                    <div className="space-y-6">
                                        {content.quiz.map((question, qIdx) => (
                                            <div key={question.id} className="border border-gray-200 rounded-lg p-6">
                                                <p className="font-semibold text-gray-900 mb-4">
                                                    {qIdx + 1}. {question.question}
                                                </p>

                                                <div className="space-y-2">
                                                    {question.options.map((option, oIdx) => (
                                                        <label
                                                            key={oIdx}
                                                            className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-blue-50 cursor-pointer transition"
                                                        >
                                                            <input
                                                                type="radio"
                                                                name={question.id}
                                                                value={oIdx}
                                                                checked={quizAnswers[question.id] === oIdx}
                                                                onChange={() => setQuizAnswers(prev => ({ ...prev, [question.id]: oIdx }))}
                                                                className="mr-3"
                                                            />
                                                            <span className="text-gray-700">{option}</span>
                                                        </label>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}

                                        <button
                                            onClick={handleQuizSubmit}
                                            disabled={Object.keys(quizAnswers).length < content.quiz.length}
                                            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                        >
                                            Submit Quiz
                                        </button>
                                    </div>
                                ) : (
                                    <div>
                                        <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6 mb-6 text-center">
                                            <h3 className="text-2xl font-bold text-gray-900 mb-2">Quiz Results</h3>
                                            <p className="text-4xl font-bold text-blue-600">{calculateQuizScore()}%</p>
                                            <p className="text-gray-600 mt-2">
                                                {Object.values(quizAnswers).filter((ans, idx) => ans === content.quiz[idx].correct_answer).length} / {content.quiz.length} correct
                                            </p>
                                        </div>

                                        <div className="space-y-6">
                                            {content.quiz.map((question, qIdx) => {
                                                const userAnswer = quizAnswers[question.id];
                                                const isCorrect = userAnswer === question.correct_answer;

                                                return (
                                                    <div key={question.id} className={`border-2 rounded-lg p-6 ${isCorrect ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'
                                                        }`}>
                                                        <p className="font-semibold text-gray-900 mb-4">
                                                            {qIdx + 1}. {question.question}
                                                        </p>

                                                        <div className="space-y-2 mb-4">
                                                            {question.options.map((option, oIdx) => (
                                                                <div
                                                                    key={oIdx}
                                                                    className={`p-3 rounded-lg ${oIdx === question.correct_answer
                                                                        ? 'bg-green-200 border-2 border-green-600'
                                                                        : oIdx === userAnswer
                                                                            ? 'bg-red-200 border-2 border-red-600'
                                                                            : 'bg-white border border-gray-200'
                                                                        }`}
                                                                >
                                                                    {oIdx === question.correct_answer && '✓ '}
                                                                    {oIdx === userAnswer && oIdx !== question.correct_answer && '✗ '}
                                                                    {option}
                                                                </div>
                                                            ))}
                                                        </div>

                                                        <div className="bg-white rounded-lg p-4">
                                                            <p className="font-semibold text-gray-900 mb-1">Explanation:</p>
                                                            <p className="text-gray-700">{question.explanation}</p>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mx-auto mb-4"></div>
                                <p className="text-gray-600 text-lg">Generating quiz questions...</p>
                                <p className="text-gray-500 text-sm mt-2">This usually takes 1-2 minutes</p>
                            </div>
                        )
                    )}
                </div>
            </div>
        </div >
    );
}
