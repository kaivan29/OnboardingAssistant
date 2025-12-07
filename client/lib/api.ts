const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ResumeAnalysis {
    background: string;
    skills: string[];
    experience_level: string;
    strengths: string[];
    learning_areas: string[];
    ramp_up_expectation?: string;
}

export interface Candidate {
    id: number;
    name: string;
    email: string;
    resume_analysis?: ResumeAnalysis;
    created_at: string;
}

export interface WeekPlan {
    week_number: number;
    title: string;
    objectives: string[];
    topics: string[];
}

export interface LearningPlan {
    id: number;
    candidate_id: number;
    codebase_url: string;
    weeks: WeekPlan[];
    created_at: string;
}

export interface WeeklyReading {
    title: string;
    content: string;
    key_concepts: string[];
    resources: string[];
    reason?: string;
}

export interface CodingTask {
    id: string;
    title: string;
    description: string;
    difficulty: string;
    estimated_time: string;
    files_to_modify: string[];
    hints: string[];
    reason?: string;
}

export interface QuizQuestion {
    id: string;
    question: string;
    options: string[];
    correct_answer: number;
    explanation: string;
}

export interface WeeklyContent {
    week_number: number;
    reading_material: WeeklyReading;
    coding_tasks: CodingTask[];
    quiz: QuizQuestion[];
}

export const api = {
    async uploadResume(file: File, name: string, email: string): Promise<Candidate> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', name);
        formData.append('email', email);

        // Upload returns immediately - analysis happens in background
        const response = await fetch(`${API_BASE_URL}/api/upload-resume`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error('Failed to upload resume');
        }

        return response.json();
    },

    async getCandidateStatus(candidateId: number): Promise<{
        id: number;
        name: string;
        analysis_complete: boolean;
        resume_analysis: ResumeAnalysis | null;
    }> {
        const response = await fetch(`${API_BASE_URL}/api/candidate/${candidateId}/status`);

        if (!response.ok) {
            throw new Error('Failed to get candidate status');
        }

        return response.json();
    },

    async analyzeCodebase(codebaseUrl: string, githubToken?: string): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/api/analyze-codebase`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                codebase_url: codebaseUrl,
                github_token: githubToken,
            }),
        });

        if (!response.ok) {
            throw new Error('Failed to analyze codebase');
        }

        return response.json();
    },

    async generateLearningPlan(
        candidateId: number,
        codebaseUrl: string,
        githubToken?: string
    ): Promise<LearningPlan> {
        const response = await fetch(`${API_BASE_URL}/api/generate-plan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                candidate_id: candidateId,
                codebase_url: codebaseUrl,
                github_token: githubToken,
            }),
        });

        if (!response.ok) {
            throw new Error('Failed to generate learning plan');
        }

        return response.json();
    },

    async getLearningPlan(candidateId: number): Promise<LearningPlan> {
        const response = await fetch(`${API_BASE_URL}/api/plan/${candidateId}`);

        if (!response.ok) {
            throw new Error('Failed to get learning plan');
        }

        return response.json();
    },

    async getWeeklyContent(candidateId: number, weekNumber: number): Promise<WeeklyContent> {
        const response = await fetch(`${API_BASE_URL}/api/week/${candidateId}/${weekNumber}`);

        if (!response.ok) {
            throw new Error('Failed to get weekly content');
        }

        return response.json();
    },

    async updateProgress(
        candidateId: number,
        weekNumber: number,
        data: {
            reading_completed?: boolean;
            task_id?: string;
            quiz_answers?: number[];
        }
    ): Promise<void> {
        const response = await fetch(`${API_BASE_URL}/api/progress/${candidateId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                week_number: weekNumber,
                ...data,
            }),
        });

        if (!response.ok) {
            throw new Error('Failed to update progress');
        }
    },

    async markChapterComplete(candidateId: number, weekNumber: number, chapterNumber: number): Promise<{ message: string; completed_chapters: number[] }> {
        const response = await fetch(`${API_BASE_URL}/api/progress/${candidateId}/week/${weekNumber}/chapter/${chapterNumber}/complete`, {
            method: 'POST',
        });

        if (!response.ok) {
            throw new Error('Failed to mark chapter complete');
        }

        return response.json();
    },

    async getWeekProgress(candidateId: number, weekNumber: number): Promise<{
        candidate_id: number;
        week_number: number;
        completed_chapters: number[];
        completed_tasks: string[];
        quiz_score: number | null;
        quiz_answers: number[] | null;
    }> {
        const response = await fetch(`${API_BASE_URL}/api/progress/${candidateId}/week/${weekNumber}`);

        if (!response.ok) {
            throw new Error('Failed to get week progress');
        }

        return response.json();
    },

    async getCandidates(): Promise<Candidate[]> {
        const response = await fetch(`${API_BASE_URL}/api/candidates`);

        if (!response.ok) {
            throw new Error('Failed to get candidates');
        }

        return response.json();
    },

    async getCodebaseFiles(codebaseId: string, path: string = ''): Promise<{ files: FileNode[] }> {
        const response = await fetch(`${API_BASE_URL}/api/codebase/${codebaseId}/files?path=${encodeURIComponent(path)}`);

        if (!response.ok) {
            throw new Error('Failed to get codebase files');
        }

        return response.json();
    },

    async getFileContent(codebaseId: string, path: string): Promise<{ content: string }> {
        const response = await fetch(`${API_BASE_URL}/api/codebase/${codebaseId}/content?path=${encodeURIComponent(path)}`);

        if (!response.ok) {
            throw new Error('Failed to get file content');
        }

        return response.json();
    },

    async getCourseProgress(candidateId: number): Promise<{
        progress: number;
        tasks_completed: number;
        total_weeks: number;
        weeks_progress?: { week_number: number; percent: number; is_complete: boolean }[];
    }> {
        const response = await fetch(`${API_BASE_URL}/api/progress/${candidateId}/overall`);
        if (!response.ok) {
            throw new Error('Failed to get course progress');
        }
        return response.json();
    },
};

export interface FileNode {
    name: string;
    path: string;
    type: 'file' | 'dir';
    size: number;
}
