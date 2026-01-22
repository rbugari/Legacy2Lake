"use client";

import React, { useCallback } from 'react';
import {
    ReactFlow,
    useNodesState,
    useEdgesState,
    addEdge,
    Background,
    Controls,
    MiniMap,
    ConnectionMode,
    useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import CustomNode from './CustomNode';
import dagre from 'dagre';
import { Columns, Rows, Maximize } from 'lucide-react';

const nodeTypes = {
    custom: CustomNode,
    customNode: CustomNode,
    default: CustomNode,
};

const defaultNodes = [
    { id: '1', position: { x: 100, y: 100 }, data: { label: 'Waiting for upload...' }, type: 'input' },
];

const defaultEdges = [] as any[];

interface MeshGraphProps {
    nodes?: any[];
    edges?: any[];
    onNodesChange?: any;
    onEdgesChange?: any;
    onConnect?: any;
    onNodeClick?: (node: any) => void;
    onNodeDragStop?: (event: any, node: any, nodes: any[]) => void;
    onInit?: (instance: any) => void;
    onDrop?: (event: React.DragEvent) => void;
    onDragOver?: (event: React.DragEvent) => void;
    onNodesDelete?: (nodes: any[]) => void;
    onEdgesDelete?: (edges: any[]) => void;
}

export default function MeshGraph({
    nodes: propNodes,
    edges: propEdges,
    onNodesChange: propOnNodesChange,
    onEdgesChange: propOnEdgesChange,
    onConnect: propOnConnect,
    onNodeClick,
    onNodeDragStop,
    onInit,
    onDrop,
    onDragOver,
    onNodesDelete,
    onEdgesDelete
}: MeshGraphProps) {
    // Internal state fallback if not controlled
    const [internalNodes, setInternalNodes, onInternalNodesChange] = useNodesState(defaultNodes);
    const [internalEdges, setInternalEdges, onInternalEdgesChange] = useEdgesState(defaultEdges);

    const nodes = propNodes || internalNodes;
    const edges = propEdges || internalEdges;
    const onNodesChange = propOnNodesChange || onInternalNodesChange;
    const onEdgesChange = propOnEdgesChange || onInternalEdgesChange;

    const onConnect = useCallback(
        (params: any) => {
            if (propOnConnect) {
                propOnConnect(params);
            } else {
                setInternalEdges((eds) => addEdge(params, eds));
            }
        },
        [propOnConnect, setInternalEdges],
    );

    const { fitView } = useReactFlow();

    const onLayout = useCallback((direction: 'TB' | 'LR') => {
        const dagreGraph = new dagre.graphlib.Graph();
        dagreGraph.setDefaultEdgeLabel(() => ({}));

        dagreGraph.setGraph({
            rankdir: direction,
            nodesep: 80,
            ranksep: 100,
            marginx: 50,
            marginy: 50
        });

        nodes.forEach((node: any) => {
            dagreGraph.setNode(node.id, { width: 260, height: 140 });
        });

        edges.forEach((edge: any) => {
            dagreGraph.setEdge(edge.source, edge.target);
        });

        dagre.layout(dagreGraph);

        const newNodes = nodes.map((node: any) => {
            const nodeWithPosition = dagreGraph.node(node.id);
            return {
                ...node,
                position: {
                    x: nodeWithPosition.x - 130,
                    y: nodeWithPosition.y - 70,
                },
            };
        });

        onNodesChange(newNodes.map((n: any) => ({ type: 'reset', item: n })));

        // Ensure nodes have rendered at new positions before fitting
        setTimeout(() => {
            fitView({ duration: 800, padding: 0.2 });
        }, 50);
    }, [nodes, edges, onNodesChange, fitView]);

    return (
        <div
            className="h-full w-full bg-[var(--background)] rounded-xl border border-[var(--border)] overflow-hidden shadow-inner relative"
            onDrop={onDrop}
            onDragOver={onDragOver}
        >
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onNodeClick={(_, node) => onNodeClick?.(node)}
                onNodeDragStop={(evt, node, nodes) => onNodeDragStop?.(evt, node, nodes)}
                onInit={onInit}
                onNodesDelete={onNodesDelete}
                onEdgesDelete={onEdgesDelete}
                nodeTypes={nodeTypes}
                connectionMode={ConnectionMode.Loose}
                fitView
            >
                <Background color="var(--text-secondary)" gap={20} className="opacity-10" />
                <Controls showInteractive={false} className="!bg-[var(--surface)]/50 !border-none !shadow-none opacity-50 hover:opacity-100 transition-opacity" />
                <MiniMap zoomable pannable className="!bg-[var(--surface)]/50 !border-none !shadow-none opacity-20 hover:opacity-80 transition-opacity" />

                {/* Custom Layout Toolbar - Relocated and minimized */}
                <div className="absolute bottom-4 right-4 z-50 flex gap-0.5 bg-[var(--surface)]/90 p-1 rounded-lg border border-[var(--border)] shadow-md backdrop-blur-md">
                    <button
                        onClick={() => onLayout('TB')}
                        className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors text-gray-500 dark:text-gray-400"
                        title="Orden Vertical"
                    >
                        <Rows size={14} />
                    </button>
                    <button
                        onClick={() => onLayout('LR')}
                        className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors text-gray-500 dark:text-gray-400"
                        title="Orden Horizontal"
                    >
                        <Columns size={14} />
                    </button>
                    <div className="w-px h-3 bg-gray-200 dark:bg-gray-700 my-auto mx-0.5" />
                    <button
                        onClick={() => fitView({ duration: 400 })}
                        className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors text-gray-500 dark:text-gray-400"
                        title="Ajustar Vista"
                    >
                        <Maximize size={14} />
                    </button>
                </div>
            </ReactFlow>
        </div>
    );
}
