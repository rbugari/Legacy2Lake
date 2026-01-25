import React, { useState } from 'react';
import { Plus, Trash2, Code, Info } from 'lucide-react';

interface Variable {
    key: string;
    value: string;
    description?: string;
}

interface VariableEditorProps {
    variables: Variable[];
    onChange: (variables: Variable[]) => void;
}

export default function VariableEditor({ variables, onChange }: VariableEditorProps) {
    const [newKey, setNewKey] = useState("");
    const [newValue, setNewValue] = useState("");

    const handleAdd = () => {
        if (!newKey.trim()) return;
        const updated = [...variables, { key: newKey.toUpperCase().replace(/\s+/g, '_'), value: newValue }];
        onChange(updated);
        setNewKey("");
        setNewValue("");
    };

    const handleRemove = (index: number) => {
        const updated = variables.filter((_, i) => i !== index);
        onChange(updated);
    };

    const handleUpdate = (index: number, field: keyof Variable, val: string) => {
        const updated = [...variables];
        updated[index] = { ...updated[index], [field]: val };
        onChange(updated);
    };

    return (
        <div className="space-y-4">
            <div className="bg-amber-50 dark:bg-amber-900/10 p-4 rounded-xl border border-amber-100 dark:border-amber-900/30">
                <div className="flex gap-3">
                    <Info className="text-amber-600 shrink-0" size={20} />
                    <div>
                        <h4 className="font-bold text-amber-800 dark:text-amber-500 text-sm">Variable Injection Mode</h4>
                        <p className="text-xs text-amber-700 dark:text-amber-400 mt-1 leading-relaxed">
                            Variables defined here (e.g., <code>S3_ROOT</code>) will be automatically detected by the AI Engine.
                            If a generated code path matches a variable's value, it will be replaced with the placeholder (e.g. <code>{`{S3_ROOT}`}</code>).
                        </p>
                    </div>
                </div>
            </div>

            <div className="border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden">
                <table className="w-full text-sm text-left">
                    <thead className="bg-gray-50 dark:bg-gray-900 text-gray-500 font-bold border-b border-gray-200 dark:border-gray-800">
                        <tr>
                            <th className="px-4 py-3 w-1/3">Variable Name</th>
                            <th className="px-4 py-3 w-1/2">Value (e.g. Path)</th>
                            <th className="px-4 py-3 w-12 text-center">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                        {variables.map((v, i) => (
                            <tr key={i} className="group hover:bg-gray-50 dark:hover:bg-gray-900/30">
                                <td className="px-4 py-2">
                                    <div className="flex items-center gap-2">
                                        <Code size={14} className="text-gray-300" />
                                        <input
                                            type="text"
                                            value={v.key}
                                            onChange={(e) => handleUpdate(i, 'key', e.target.value.toUpperCase())}
                                            className="bg-transparent font-mono font-bold text-blue-600 w-full outline-none"
                                            placeholder="MY_VAR"
                                        />
                                    </div>
                                </td>
                                <td className="px-4 py-2">
                                    <input
                                        type="text"
                                        value={v.value}
                                        onChange={(e) => handleUpdate(i, 'value', e.target.value)}
                                        className="bg-transparent w-full outline-none text-gray-700 dark:text-gray-300"
                                        placeholder="Value..."
                                    />
                                </td>
                                <td className="px-4 py-2 text-center">
                                    <button
                                        onClick={() => handleRemove(i)}
                                        className="text-gray-300 hover:text-red-500 transition-colors"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                    <tfoot className="bg-gray-50 dark:bg-gray-900/50">
                        <tr>
                            <td className="px-4 py-2">
                                <input
                                    type="text"
                                    value={newKey}
                                    onChange={(e) => setNewKey(e.target.value)}
                                    className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded px-2 py-1 w-full text-xs font-mono"
                                    placeholder="NEW_VAR_NAME"
                                />
                            </td>
                            <td className="px-4 py-2">
                                <input
                                    type="text"
                                    value={newValue}
                                    onChange={(e) => setNewValue(e.target.value)}
                                    className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded px-2 py-1 w-full text-xs"
                                    placeholder="Value..."
                                    onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
                                />
                            </td>
                            <td className="px-4 py-2 text-center">
                                <button
                                    onClick={handleAdd}
                                    disabled={!newKey}
                                    className="bg-blue-500 text-white p-1 rounded hover:bg-blue-600 disabled:opacity-50 transition-colors"
                                >
                                    <Plus size={16} />
                                </button>
                            </td>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>
    );
}
