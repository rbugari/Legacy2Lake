"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { Folder, FolderOpen, FileCode, RefreshCw, PanelLeftClose, PanelLeftOpen, ChevronDown, ChevronRight, Filter } from "lucide-react";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { fetchWithAuth } from "../lib/auth-client";

interface FileNode {
    name: string;
    path: string;
    type: "file" | "folder";
    children?: FileNode[];
    last_modified?: number;
}

interface UnifiedFileExplorerProps {
    projectId: string;
    activeTenantId?: string;
    
    // Optional customization
    showToolbar?: boolean; // Show/hide toolbar (default true)
    readOnly?: boolean; // Future: disable editing (default true)
    onFileSelect?: (file: FileNode) => void; // Custom callback on file select
    variant?: 'full' | 'compact'; // Layout variant (default 'full')
    title?: string; // Custom title (default "Solution Output")
    autoExpandDepth?: number; // Auto-expand folders to this depth (default 2)
}

// Format date as yy-mm-dd hh:mm for easy identification of old files
function formatFileDate(timestamp: number): string {
    const date = new Date(timestamp * 1000);
    const yy = String(date.getFullYear()).slice(-2);
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    const hh = String(date.getHours()).padStart(2, '0');
    const min = String(date.getMinutes()).padStart(2, '0');
    return `${yy}-${mm}-${dd} ${hh}:${min}`;
}

export default function UnifiedFileExplorer({
    projectId,
    activeTenantId,
    showToolbar = true,
    readOnly = true,
    onFileSelect: customOnFileSelect,
    variant = 'full',
    title = "Solution Output",
    autoExpandDepth = 2
}: UnifiedFileExplorerProps) {
    const [tree, setTree] = useState<FileNode | null>(null);
    const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
    const [fileContent, setFileContent] = useState<string>("");
    const [loadingContent, setLoadingContent] = useState(false);
    const [selectedFileType, setSelectedFileType] = useState<string>("all");

    // UI Logic for Resizing and Toggling
    const [isTreeVisible, setIsTreeVisible] = useState(true);
    const [treeWidth, setTreeWidth] = useState(variant === 'compact' ? 200 : 300); // px
    const isResizing = useRef(false);

    // Persist tree width & visibility
    useEffect(() => {
        const saved = localStorage.getItem(`tree-width-${projectId}`);
        if (saved) setTreeWidth(parseInt(saved));
        const visible = localStorage.getItem(`tree-visible-${projectId}`);
        if (visible !== null) setIsTreeVisible(visible === 'true');
    }, [projectId]);

    const handleToggleTree = () => {
        const next = !isTreeVisible;
        setIsTreeVisible(next);
        localStorage.setItem(`tree-visible-${projectId}`, String(next));
    };

    const startResizing = useCallback((e: React.MouseEvent) => {
        isResizing.current = true;
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', stopResizing);
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        document.body.classList.add('resizing');
    }, []);

    const stopResizing = useCallback(() => {
        isResizing.current = false;
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', stopResizing);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        document.body.classList.remove('resizing');
        localStorage.setItem(`tree-width-${projectId}`, String(treeWidth));
    }, [projectId, treeWidth]);

    const handleMouseMove = useCallback((e: MouseEvent) => {
        if (!isResizing.current) return;
        const container = document.getElementById(`file-explorer-${projectId}`);
        if (container) {
            const rect = container.getBoundingClientRect();
            const newWidth = e.clientX - rect.left;
            if (newWidth > 150 && newWidth < 800) {
                setTreeWidth(newWidth);
            }
        }
    }, [projectId]);

    const loadFiles = async () => {
        try {
            const res = await fetchWithAuth(`projects/${projectId}/files`, {
                headers: activeTenantId ? { "X-Tenant-ID": activeTenantId } : {}
            });
            const data = await res.json();
            setTree(data);
        } catch (e) {
            console.error("[UnifiedFileExplorer] Files error", e);
        }
    };

    const handleFileSelect = async (node: FileNode) => {
        if (node.type !== "file") return;

        setSelectedFile(node);
        setLoadingContent(true);
        setFileContent("");

        // Call custom callback if provided
        if (customOnFileSelect) {
            customOnFileSelect(node);
        }

        try {
            // Encode path to handle slashes correctly
            const res = await fetchWithAuth(`projects/${projectId}/files/content?path=${encodeURIComponent(node.path)}`, {
                headers: activeTenantId ? { "X-Tenant-ID": activeTenantId } : {}
            });
            const data = await res.json();
            if (data.content !== undefined) {
                setFileContent(data.content);
            } else {
                setFileContent(`Error loading file: ${data.error}`);
            }
        } catch (e) {
            setFileContent(`Network error: ${e}`);
        } finally {
            setLoadingContent(false);
        }
    };

    useEffect(() => {
        loadFiles();
    }, [projectId]);

    // Determine language from file extension
    const getLanguage = (filename: string): string => {
        if (filename.endsWith('.py')) return 'python';
        if (filename.endsWith('.sql')) return 'sql';
        if (filename.endsWith('.json')) return 'json';
        if (filename.endsWith('.md')) return 'markdown';
        if (filename.endsWith('.js') || filename.endsWith('.jsx')) return 'javascript';
        if (filename.endsWith('.ts') || filename.endsWith('.tsx')) return 'typescript';
        if (filename.endsWith('.yaml') || filename.endsWith('.yml')) return 'yaml';
        if (filename.endsWith('.xml')) return 'xml';
        if (filename.endsWith('.html')) return 'html';
        if (filename.endsWith('.css')) return 'css';
        if (filename.endsWith('.sh')) return 'bash';
        return 'text';
    };

    // Extract all unique file extensions from tree
    const getAvailableExtensions = (node: FileNode | null): string[] => {
        if (!node) return [];
        const extensions = new Set<string>();
        
        const traverse = (n: FileNode) => {
            if (n.type === 'file') {
                const ext = n.name.includes('.') ? '.' + n.name.split('.').pop() : '.txt';
                extensions.add(ext);
            }
            if (n.children) {
                n.children.forEach(traverse);
            }
        };
        
        traverse(node);
        return Array.from(extensions).sort();
    };

    // Filter tree by file extension
    const filterTreeByExtension = (node: FileNode | null, extension: string): FileNode | null => {
        if (!node) return null;
        if (extension === 'all') return node;

        const filterNode = (n: FileNode): FileNode | null => {
            if (n.type === 'file') {
                const fileExt = '.' + n.name.split('.').pop();
                return fileExt === extension ? n : null;
            }
            
            // For folders, recursively filter children
            if (n.children) {
                const filteredChildren = n.children
                    .map(child => filterNode(child))
                    .filter(child => child !== null) as FileNode[];
                
                // Only include folder if it has matching children
                if (filteredChildren.length > 0) {
                    return { ...n, children: filteredChildren };
                }
            }
            
            return null;
        };

        return filterNode(node);
    };

    // Memoize available extensions and filtered tree
    const availableExtensions = useMemo(() => getAvailableExtensions(tree), [tree]);
    const filteredTree = useMemo(() => filterTreeByExtension(tree, selectedFileType), [tree, selectedFileType]);

    return (
        <div id={`file-explorer-${projectId}`} className="h-full flex flex-col bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Toolbar */}
            {showToolbar && (
                <div className="p-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gradient-to-r from-blue-50 to-gray-50 dark:from-blue-950/20 dark:to-gray-900 shrink-0">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={handleToggleTree}
                            className={`p-1.5 rounded-lg transition-all ${
                                isTreeVisible 
                                    ? "bg-blue-500/10 text-blue-500 border border-blue-500/20 shadow-sm" 
                                    : "text-gray-400 hover:text-white border border-transparent hover:bg-gray-800"
                            }`}
                            title={isTreeVisible ? "Hide Library" : "Show Library"}
                        >
                            {isTreeVisible ? <PanelLeftClose size={16} /> : <PanelLeftOpen size={16} />}
                        </button>
                        <div className="flex items-center gap-2">
                            <span className="font-bold text-sm flex items-center gap-2 text-gray-700 dark:text-gray-200">
                                <Folder size={16} className="text-blue-500" /> {title}
                            </span>
                            <span className="px-2 py-0.5 text-[10px] font-black uppercase tracking-wider bg-blue-500 text-white rounded-md shadow-sm">
                                Enhanced
                            </span>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {/* File Type Filter */}
                        <div className="flex items-center gap-1.5">
                            <Filter size={12} className="text-gray-400" />
                            <select
                                value={selectedFileType}
                                onChange={(e) => setSelectedFileType(e.target.value)}
                                className="text-xs bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
                            >
                                <option value="all">All Files</option>
                                {availableExtensions.map(ext => (
                                    <option key={ext} value={ext}>
                                        {ext} files
                                    </option>
                                ))}
                            </select>
                        </div>
                        <button 
                            onClick={loadFiles} 
                            className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-all" 
                            title="Refresh Files"
                        >
                            <RefreshCw size={14} />
                        </button>
                    </div>
                </div>
            )}

            {/* Split Pane Content */}
            <div className="flex-1 flex overflow-hidden relative">
                {/* Left Pane: File Tree */}
                {isTreeVisible && (
                    <div
                        className="border-r border-gray-200 dark:border-gray-700 overflow-y-auto p-2 bg-gray-50/50 dark:bg-gray-900/50 shrink-0"
                        style={{ width: `${treeWidth}px` }}
                    >
                        {filteredTree ? (
                            <div className="space-y-1">
                                <FileTree
                                    node={filteredTree}
                                    level={0}
                                    onSelect={handleFileSelect}
                                    selectedPath={selectedFile?.path}
                                    autoExpandDepth={autoExpandDepth}
                                />
                            </div>
                        ) : tree ? (
                            <div className="text-center p-10 text-gray-400">
                                <Filter className="mx-auto mb-2 opacity-50" size={32} />
                                <p className="text-sm">No files match filter</p>
                                <button
                                    onClick={() => setSelectedFileType('all')}
                                    className="mt-2 text-xs text-blue-500 hover:text-blue-400 underline"
                                >
                                    Clear filter
                                </button>
                            </div>
                        ) : (
                            <div className="text-center p-4 text-gray-400">Loading files...</div>
                        )}

                        {filteredTree && filteredTree.children?.length === 0 && (
                            <div className="text-center p-10 text-gray-400">
                                <Folder className="mx-auto mb-2 opacity-50" size={32} />
                                <p className="text-sm">Empty Output</p>
                            </div>
                        )}
                    </div>
                )}

                {/* Resize Handle */}
                {isTreeVisible && (
                    <div
                        onMouseDown={startResizing}
                        className="w-1.5 bg-transparent hover:bg-blue-500/30 cursor-col-resize transition-all z-20 absolute top-0 bottom-0 select-none group"
                        style={{ left: `${treeWidth}px`, marginLeft: '-3px' }}
                    >
                        <div className="absolute inset-y-0 left-1/2 w-0.5 bg-gray-200 dark:bg-gray-700 group-hover:bg-blue-500 transition-colors opacity-0 group-hover:opacity-100" />
                    </div>
                )}

                {/* Right Pane: Code Preview */}
                <div className="flex-1 bg-white dark:bg-gray-950 overflow-hidden flex flex-col min-w-0">
                    {selectedFile ? (
                        <>
                            <div className="p-2 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 text-xs font-mono text-gray-500 flex justify-between shrink-0">
                                <span className="truncate">{selectedFile.path}</span>
                                {selectedFile.last_modified && (
                                    <span className="whitespace-nowrap ml-4">
                                        Generated: {formatFileDate(selectedFile.last_modified)}
                                    </span>
                                )}
                            </div>
                            <div className="flex-1 overflow-auto custom-scrollbar min-h-0">
                                {loadingContent ? (
                                    <div className="flex items-center justify-center h-full text-gray-400 gap-2">
                                        <RefreshCw size={16} className="animate-spin" /> Loading content...
                                    </div>
                                ) : (() => {
                                    // Data/config files: wrap long lines to fit the panel
                                    // Code files: keep horizontal scroll (no forced wrap)
                                    const wrapLong = /\.(json|yaml|yml|xml|md|html|css|txt)$/i.test(selectedFile.name);
                                    return (
                                        <div className={wrapLong ? "w-full" : "min-w-max"}>
                                            <SyntaxHighlighter
                                                language={getLanguage(selectedFile.name)}
                                                style={vscDarkPlus}
                                                customStyle={{ 
                                                    margin: 0, 
                                                    padding: variant === 'compact' ? '1rem' : '1.5rem', 
                                                    background: '#0a0a0a', 
                                                    fontSize: variant === 'compact' ? '12px' : '13px', 
                                                    lineHeight: '1.5',
                                                    whiteSpace: wrapLong ? 'pre-wrap' : 'pre',
                                                    wordBreak: wrapLong ? 'break-all' : undefined,
                                                }}
                                                showLineNumbers={true}
                                                wrapLines={wrapLong}
                                                wrapLongLines={wrapLong}
                                            >
                                                {fileContent}
                                            </SyntaxHighlighter>
                                        </div>
                                    );
                                })()}
                            </div>
                        </>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-400">
                            <FileCode size={48} className="mb-4 opacity-20" />
                            <p className="text-sm">Select a file to view content</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// Recursive File Tree Component
function FileTree({ 
    node, 
    level, 
    onSelect, 
    selectedPath,
    autoExpandDepth = 2
}: { 
    node: FileNode; 
    level: number; 
    onSelect: (n: FileNode) => void; 
    selectedPath?: string;
    autoExpandDepth?: number;
}) {
    const [isOpen, setIsOpen] = useState(level < autoExpandDepth); // Auto-expand based on depth
    const isFolder = node.type === "folder";
    const isSelected = node.path === selectedPath;

    return (
        <div className="ml-2">
            <div
                className={`flex items-center gap-2 py-1.5 px-2 rounded cursor-pointer text-sm transition-colors group justify-between ${
                    isSelected
                        ? "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300"
                        : "hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
                }`}
                onClick={(e) => {
                    e.stopPropagation();
                    if (isFolder) setIsOpen(!isOpen);
                    else onSelect(node);
                }}
            >
                <div className="flex items-center gap-2 truncate">
                    <span className="text-gray-400 shrink-0">
                        {isFolder ? (
                            isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />
                        ) : (
                            <span className="w-3.5" />
                        )}
                    </span>
                    {isFolder ? (
                        <Folder size={14} className="text-blue-500 shrink-0" />
                    ) : (
                        <FileCode size={14} className="text-orange-500 shrink-0" />
                    )}
                    <span className="truncate">{node.name}</span>
                </div>

                {/* Date Display - Always visible to check if file is old */}
                {!isFolder && node.last_modified && (
                    <span className="text-[10px] text-gray-400 whitespace-nowrap font-mono ml-2">
                        {formatFileDate(node.last_modified)}
                    </span>
                )}
            </div>

            {isFolder && isOpen && node.children && (
                <div className="border-l border-gray-200 dark:border-gray-700 ml-3 pl-1">
                    {node.children.map((child, i) => (
                        <FileTree
                            key={i}
                            node={child}
                            level={level + 1}
                            onSelect={onSelect}
                            selectedPath={selectedPath}
                            autoExpandDepth={autoExpandDepth}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
