import { useState, useEffect, useCallback, useRef } from "react";
import { Folder, FolderOpen, FileCode, RefreshCw, PanelLeftClose, PanelLeftOpen, ChevronDown, ChevronRight } from "lucide-react";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { fetchWithAuth } from "../../lib/auth-client";

interface FileNode {
    name: string;
    path: string;
    type: "file" | "folder";
    children?: FileNode[];
    last_modified?: number;
}

interface FileManagerTabProps {
    projectId: string;
    activeTenantId?: string;
}

export default function FileManagerTab({ projectId, activeTenantId }: FileManagerTabProps) {
    const [tree, setTree] = useState<FileNode | null>(null);
    const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
    const [fileContent, setFileContent] = useState<string>("");
    const [loadingContent, setLoadingContent] = useState(false);

    // UI Logic for Resizing and Toggling
    const [isTreeVisible, setIsTreeVisible] = useState(true);
    const [treeWidth, setTreeWidth] = useState(300); // px
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
        const container = document.getElementById('file-explorer-container');
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
            console.error("Files error", e);
        }
    };

    const handleFileSelect = async (node: FileNode) => {
        if (node.type !== "file") return;

        setSelectedFile(node);
        setLoadingContent(true);
        setFileContent("");

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

    return (
        <div id="file-explorer-container" className="h-full flex flex-col bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Toolbar */}
            <div className="p-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900 shrink-0">
                <div className="flex items-center gap-3">
                    <button
                        onClick={handleToggleTree}
                        className={`p-1.5 rounded-lg transition-all ${isTreeVisible ? "bg-blue-500/10 text-blue-500 border border-blue-500/20 shadow-sm" : "text-gray-400 hover:text-white border border-transparent hover:bg-gray-800"}`}
                        title={isTreeVisible ? "Hide Library" : "Show Library"}
                    >
                        {isTreeVisible ? <PanelLeftClose size={16} /> : <PanelLeftOpen size={16} />}
                    </button>
                    <span className="font-bold text-sm flex items-center gap-2 text-gray-700 dark:text-gray-200"><Folder size={16} className="text-blue-500" /> Solution Output</span>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={loadFiles} className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-all" title="Refresh Files"><RefreshCw size={14} /></button>
                </div>
            </div>

            {/* Split Pane Content */}
            <div className="flex-1 flex overflow-hidden relative">
                {/* Left Pane: File Tree */}
                {isTreeVisible && (
                    <div
                        className="border-r border-gray-200 dark:border-gray-700 overflow-y-auto p-2 bg-gray-50/50 dark:bg-gray-900/50 shrink-0"
                        style={{ width: `${treeWidth}px` }}
                    >
                        {tree ? (
                            <div className="space-y-1">
                                <FileTree
                                    node={tree}
                                    level={0}
                                    onSelect={handleFileSelect}
                                    selectedPath={selectedFile?.path}
                                />
                            </div>
                        ) : (
                            <div className="text-center p-4 text-gray-400">Loading files...</div>
                        )}

                        {tree && tree.children?.length === 0 && (
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

                {/* Right Pane: Code Preview (flex-1 covers remaining) */}
                <div className="flex-1 bg-white dark:bg-gray-950 overflow-hidden flex flex-col min-w-0">
                    {selectedFile ? (
                        <>
                            <div className="p-2 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 text-xs font-mono text-gray-500 flex justify-between shrink-0">
                                <span>{selectedFile.name}</span>
                                {selectedFile.last_modified && (
                                    <span>Generated: {new Date(selectedFile.last_modified * 1000).toLocaleString()}</span>
                                )}
                            </div>
                            <div className="flex-1 overflow-auto custom-scrollbar min-h-0">
                                {loadingContent ? (
                                    <div className="flex items-center justify-center h-full text-gray-400 gap-2">
                                        <RefreshCw size={16} className="animate-spin" /> Loading content...
                                    </div>
                                ) : (
                                    <div className="min-w-max">
                                        <SyntaxHighlighter
                                            language={selectedFile.name.endsWith('.py') ? 'python' : selectedFile.name.endsWith('.sql') ? 'sql' : selectedFile.name.endsWith('.json') ? 'json' : selectedFile.name.endsWith('.md') ? 'markdown' : 'text'}
                                            style={vscDarkPlus}
                                            customStyle={{ margin: 0, padding: '1.5rem', background: '#0a0a0a', fontSize: '13px', lineHeight: '1.5', maxWidth: '100%' }}
                                            showLineNumbers={true}
                                            wrapLines={false}
                                        >
                                            {fileContent}
                                        </SyntaxHighlighter>
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-400">
                            <FileCode size={48} className="mb-4 opacity-20" />
                            <p>Select a file to view content</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function FileTree({ node, level, onSelect, selectedPath }: { node: FileNode, level: number, onSelect: (n: FileNode) => void, selectedPath?: string }) {
    const [isOpen, setIsOpen] = useState(level < 2); // Default open top levels
    const isFolder = node.type === "folder";
    const isSelected = node.path === selectedPath;

    return (
        <div className="ml-2">
            <div
                className={`flex items-center gap-2 py-1.5 px-2 rounded cursor-pointer text-sm transition-colors group justify-between ${isSelected
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
                        {isFolder ? (isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />) : <span className="w-3.5" />}
                    </span>
                    {isFolder ? <Folder size={14} className="text-blue-500 shrink-0" /> : <FileCode size={14} className="text-orange-500 shrink-0" />}
                    <span className="truncate">{node.name}</span>
                </div>

                {/* Date Display (Compact) */}
                {!isFolder && node.last_modified && (
                    <span className="text-[10px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap hidden xl:block">
                        {new Date(node.last_modified * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
