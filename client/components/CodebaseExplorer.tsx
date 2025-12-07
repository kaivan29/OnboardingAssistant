import { useState, useEffect } from 'react';
import { Folder, FileText, ChevronRight, ChevronDown, Code, ArrowLeft } from 'lucide-react';
import { api, FileNode } from '@/lib/api';

interface CodebaseExplorerProps {
    codebaseId: string;
}

export default function CodebaseExplorer({ codebaseId }: CodebaseExplorerProps) {
    const [currentPath, setCurrentPath] = useState('');
    const [files, setFiles] = useState<FileNode[]>([]);
    const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
    const [fileContent, setFileContent] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [contentLoading, setContentLoading] = useState(false);
    const [pathHistory, setPathHistory] = useState<string[]>([]);

    // Fetch files when path changes
    useEffect(() => {
        loadFiles(currentPath);
    }, [currentPath, codebaseId]);

    // Fetch content when file selected
    useEffect(() => {
        if (selectedFile) {
            loadFileContent(selectedFile.path);
        } else {
            setFileContent(null);
        }
    }, [selectedFile, codebaseId]);

    const loadFiles = async (path: string) => {
        setLoading(true);
        try {
            const result = await api.getCodebaseFiles(codebaseId, path);
            setFiles(result.files);
        } catch (error) {
            console.error('Failed to load files:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadFileContent = async (path: string) => {
        setContentLoading(true);
        try {
            const result = await api.getFileContent(codebaseId, path);
            setFileContent(result.content);
        } catch (error) {
            console.error('Failed to load content:', error);
            setFileContent('Error loading file content.');
        } finally {
            setContentLoading(false);
        }
    };

    const handleNavigate = (path: string) => {
        // Add current path to history before navigating
        if (path !== currentPath) {
            setPathHistory(prev => [...prev, currentPath]);
            setCurrentPath(path);
            setSelectedFile(null);
        }
    };

    const handleGoBack = () => {
        if (pathHistory.length > 0) {
            const prev = pathHistory[pathHistory.length - 1];
            setPathHistory(prev => prev.slice(0, -1));
            setCurrentPath(prev);
            setSelectedFile(null);
        } else if (currentPath !== '') {
            // Fallback to parent dir if history is empty but we are deep
            const parent = currentPath.split('/').slice(0, -1).join('/');
            setCurrentPath(parent);
            setSelectedFile(null);
        }
    };

    return (
        <div className="flex h-[calc(100vh-200px)] border border-gray-200 rounded-xl overflow-hidden bg-white">
            {/* File Tree Sidebar */}
            <div className="w-1/3 min-w-[250px] border-r border-gray-200 flex flex-col">
                {/* Explorer Header */}
                <div className="p-3 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
                    <span className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                        <Folder className="w-4 h-4" />
                        Files
                    </span>
                    {currentPath && (
                        <button
                            onClick={handleGoBack}
                            className="p-1 hover:bg-gray-200 rounded-md text-gray-600 transition-colors"
                            title="Go Back"
                        >
                            <ArrowLeft className="w-4 h-4" />
                        </button>
                    )}
                </div>

                {/* Path Breadcrumb (Static for now, just shows current dir name) */}
                <div className="px-3 py-2 bg-gray-50 text-xs text-gray-500 font-mono border-b border-gray-100 truncate">
                    {currentPath || 'root'}
                </div>

                {/* File List */}
                <div className="flex-1 overflow-y-auto p-2">
                    {loading ? (
                        <div className="flex justify-center p-4">
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-400"></div>
                        </div>
                    ) : (
                        <div className="space-y-0.5">
                            {currentPath !== '' && files.length === 0 && (
                                <div className="text-sm text-gray-400 p-2 italic">Empty directory</div>
                            )}

                            {files.map((file) => (
                                <button
                                    key={file.path}
                                    onClick={() => file.type === 'dir' ? handleNavigate(file.path) : setSelectedFile(file)}
                                    className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors text-left
                                        ${selectedFile?.path === file.path
                                            ? 'bg-blue-50 text-blue-700 font-medium'
                                            : 'hover:bg-gray-100 text-gray-700'
                                        }`}
                                >
                                    {file.type === 'dir' ? (
                                        <Folder className={`w-4 h-4 ${selectedFile?.path === file.path ? 'text-blue-500' : 'text-yellow-500'}`} />
                                    ) : (
                                        <FileText className="w-4 h-4 text-gray-400" />
                                    )}
                                    <span className="truncate">{file.name}</span>
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Content Viewer */}
            <div className="flex-1 flex flex-col bg-slate-50 overflow-hidden">
                {selectedFile ? (
                    <>
                        {/* File Header */}
                        <div className="h-10 border-b border-gray-200 bg-white px-4 flex items-center text-sm font-medium text-gray-700 shadow-sm">
                            <FileText className="w-4 h-4 mr-2 text-gray-400" />
                            {selectedFile.name}
                            <span className="ml-auto text-xs text-gray-400">
                                {(selectedFile.size / 1024).toFixed(1)} KB
                            </span>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-auto p-4">
                            {contentLoading ? (
                                <div className="flex items-center justify-center h-full text-gray-400 gap-2">
                                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-400"></div>
                                    Loading content...
                                </div>
                            ) : (
                                <pre className="font-mono text-sm leading-relaxed text-slate-800 bg-white p-4 rounded-lg border border-gray-200 shadow-sm min-h-full">
                                    <code>{fileContent}</code>
                                </pre>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                        <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mb-4">
                            <Code className="w-8 h-8 text-gray-500" />
                        </div>
                        <p className="font-medium text-gray-600">Select a file to view content</p>
                        <p className="text-sm mt-1">Navigate the codebase using the sidebar</p>
                    </div>
                )}
            </div>
        </div>
    );
}
