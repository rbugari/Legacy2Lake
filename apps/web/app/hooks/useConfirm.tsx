"use client";

import { useState, useCallback, useRef } from 'react';
import ConfirmModal, { ConfirmModalOptions } from '@/app/components/modals/ConfirmModal';
import React from 'react';

interface ConfirmState extends ConfirmModalOptions {
    isOpen: boolean;
    resolve: ((value: boolean) => void) | null;
}

/**
 * useConfirm - drop-in replacement for window.confirm()
 *
 * Usage:
 *   const { confirm, ConfirmDialog } = useConfirm();
 *
 *   // In JSX:  <>{ConfirmDialog}</>
 *
 *   // In handler:
 *   const ok = await confirm({ variant: 'execute', title: 'Run Triage?', agents: [...] });
 *   if (!ok) return;
 */
export function useConfirm() {
    const [state, setState] = useState<ConfirmState>({
        isOpen: false,
        title: '',
        resolve: null,
    });

    const confirm = useCallback((options: ConfirmModalOptions): Promise<boolean> => {
        return new Promise<boolean>((resolve) => {
            setState({ ...options, isOpen: true, resolve });
        });
    }, []);

    const handleConfirm = useCallback(() => {
        setState(prev => { prev.resolve?.(true); return { ...prev, isOpen: false, resolve: null }; });
    }, []);

    const handleCancel = useCallback(() => {
        setState(prev => { prev.resolve?.(false); return { ...prev, isOpen: false, resolve: null }; });
    }, []);

    const ConfirmDialog = React.createElement(ConfirmModal, {
        isOpen: state.isOpen,
        onConfirm: handleConfirm,
        onCancel: handleCancel,
        variant: state.variant,
        title: state.title,
        description: state.description,
        agents: state.agents,
        lostPhases: state.lostPhases,
        confirmLabel: state.confirmLabel,
        cancelLabel: state.cancelLabel,
    });

    return { confirm, ConfirmDialog };
}
