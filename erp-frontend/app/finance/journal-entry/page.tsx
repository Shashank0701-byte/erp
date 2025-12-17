"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";

interface JournalEntryLine {
    id: string;
    accountCode: string;
    accountName: string;
    description: string;
    debit: string;
    credit: string;
}

export default function JournalEntryPage() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    // Form state
    const [entryDate, setEntryDate] = useState(
        new Date().toISOString().split("T")[0]
    );
    const [referenceNumber, setReferenceNumber] = useState("");
    const [description, setDescription] = useState("");
    const [lines, setLines] = useState<JournalEntryLine[]>([
        {
            id: "1",
            accountCode: "",
            accountName: "",
            description: "",
            debit: "",
            credit: "",
        },
        {
            id: "2",
            accountCode: "",
            accountName: "",
            description: "",
            debit: "",
            credit: "",
        },
    ]);

    const addLine = () => {
        const newLine: JournalEntryLine = {
            id: Date.now().toString(),
            accountCode: "",
            accountName: "",
            description: "",
            debit: "",
            credit: "",
        };
        setLines([...lines, newLine]);
    };

    const removeLine = (id: string) => {
        if (lines.length > 2) {
            setLines(lines.filter((line) => line.id !== id));
        }
    };

    const updateLine = (
        id: string,
        field: keyof JournalEntryLine,
        value: string
    ) => {
        setLines(
            lines.map((line) => (line.id === id ? { ...line, [field]: value } : line))
        );
    };

    const calculateTotals = () => {
        const totalDebit = lines.reduce(
            (sum, line) => sum + (parseFloat(line.debit) || 0),
            0
        );
        const totalCredit = lines.reduce(
            (sum, line) => sum + (parseFloat(line.credit) || 0),
            0
        );
        return { totalDebit, totalCredit };
    };

    const isBalanced = () => {
        const { totalDebit, totalCredit } = calculateTotals();
        return totalDebit === totalCredit && totalDebit > 0;
    };

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError("");
        setSuccess(false);

        if (!isBalanced()) {
            setError("Journal entry must be balanced (Total Debits = Total Credits)");
            return;
        }

        setIsLoading(true);

        try {
            const response = await fetch("/api/finance/journal-entry", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    entryDate,
                    referenceNumber,
                    description,
                    lines: lines.filter(
                        (line) => line.accountCode && (line.debit || line.credit)
                    ),
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || "Failed to create journal entry");
            }

            setSuccess(true);
            // Reset form after 2 seconds
            setTimeout(() => {
                router.push("/finance/journal-entries");
            }, 2000);
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred");
        } finally {
            setIsLoading(false);
        }
    };

    const { totalDebit, totalCredit } = calculateTotals();
    const difference = Math.abs(totalDebit - totalCredit);

    return (
        <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <button
                        onClick={() => router.back()}
                        className="flex items-center text-gray-600 hover:text-gray-900 mb-4 transition"
                    >
                        <svg
                            className="w-5 h-5 mr-2"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M15 19l-7-7 7-7"
                            />
                        </svg>
                        Back
                    </button>
                    <h1 className="text-3xl font-bold text-gray-900">
                        New Journal Entry
                    </h1>
                    <p className="text-gray-600 mt-2">
                        Create a new journal entry for financial transactions
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Entry Details Card */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">
                            Entry Details
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div>
                                <label
                                    htmlFor="entryDate"
                                    className="block text-sm font-medium text-gray-700 mb-2"
                                >
                                    Entry Date *
                                </label>
                                <input
                                    id="entryDate"
                                    type="date"
                                    value={entryDate}
                                    onChange={(e) => setEntryDate(e.target.value)}
                                    required
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                                />
                            </div>

                            <div>
                                <label
                                    htmlFor="referenceNumber"
                                    className="block text-sm font-medium text-gray-700 mb-2"
                                >
                                    Reference Number
                                </label>
                                <input
                                    id="referenceNumber"
                                    type="text"
                                    value={referenceNumber}
                                    onChange={(e) => setReferenceNumber(e.target.value)}
                                    placeholder="JE-2024-001"
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition placeholder:text-gray-400"
                                />
                            </div>

                            <div>
                                <label
                                    htmlFor="description"
                                    className="block text-sm font-medium text-gray-700 mb-2"
                                >
                                    Description *
                                </label>
                                <input
                                    id="description"
                                    type="text"
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    required
                                    placeholder="Brief description of the entry"
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition placeholder:text-gray-400"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Journal Lines Card */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-gray-900">
                                Journal Lines
                            </h2>
                            <button
                                type="button"
                                onClick={addLine}
                                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium text-sm"
                            >
                                <svg
                                    className="w-4 h-4 mr-2"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M12 4v16m8-8H4"
                                    />
                                </svg>
                                Add Line
                            </button>
                        </div>

                        {/* Table Header */}
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-gray-200">
                                        <th className="text-left py-3 px-2 text-sm font-semibold text-gray-700">
                                            Account Code
                                        </th>
                                        <th className="text-left py-3 px-2 text-sm font-semibold text-gray-700">
                                            Account Name
                                        </th>
                                        <th className="text-left py-3 px-2 text-sm font-semibold text-gray-700">
                                            Description
                                        </th>
                                        <th className="text-right py-3 px-2 text-sm font-semibold text-gray-700">
                                            Debit
                                        </th>
                                        <th className="text-right py-3 px-2 text-sm font-semibold text-gray-700">
                                            Credit
                                        </th>
                                        <th className="w-10"></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {lines.map((line, index) => (
                                        <tr key={line.id} className="border-b border-gray-100">
                                            <td className="py-3 px-2">
                                                <input
                                                    type="text"
                                                    value={line.accountCode}
                                                    onChange={(e) =>
                                                        updateLine(line.id, "accountCode", e.target.value)
                                                    }
                                                    placeholder="1000"
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition text-sm placeholder:text-gray-400"
                                                />
                                            </td>
                                            <td className="py-3 px-2">
                                                <input
                                                    type="text"
                                                    value={line.accountName}
                                                    onChange={(e) =>
                                                        updateLine(line.id, "accountName", e.target.value)
                                                    }
                                                    placeholder="Cash"
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition text-sm placeholder:text-gray-400"
                                                />
                                            </td>
                                            <td className="py-3 px-2">
                                                <input
                                                    type="text"
                                                    value={line.description}
                                                    onChange={(e) =>
                                                        updateLine(line.id, "description", e.target.value)
                                                    }
                                                    placeholder="Line description"
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition text-sm placeholder:text-gray-400"
                                                />
                                            </td>
                                            <td className="py-3 px-2">
                                                <input
                                                    type="number"
                                                    step="0.01"
                                                    min="0"
                                                    value={line.debit}
                                                    onChange={(e) =>
                                                        updateLine(line.id, "debit", e.target.value)
                                                    }
                                                    placeholder="0.00"
                                                    disabled={!!line.credit}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition text-sm text-right disabled:bg-gray-50 placeholder:text-gray-400"
                                                />
                                            </td>
                                            <td className="py-3 px-2">
                                                <input
                                                    type="number"
                                                    step="0.01"
                                                    min="0"
                                                    value={line.credit}
                                                    onChange={(e) =>
                                                        updateLine(line.id, "credit", e.target.value)
                                                    }
                                                    placeholder="0.00"
                                                    disabled={!!line.debit}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition text-sm text-right disabled:bg-gray-50 placeholder:text-gray-400"
                                                />
                                            </td>
                                            <td className="py-3 px-2">
                                                {lines.length > 2 && (
                                                    <button
                                                        type="button"
                                                        onClick={() => removeLine(line.id)}
                                                        className="text-red-600 hover:text-red-700 transition"
                                                    >
                                                        <svg
                                                            className="w-5 h-5"
                                                            fill="none"
                                                            stroke="currentColor"
                                                            viewBox="0 0 24 24"
                                                        >
                                                            <path
                                                                strokeLinecap="round"
                                                                strokeLinejoin="round"
                                                                strokeWidth={2}
                                                                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                                            />
                                                        </svg>
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                                <tfoot>
                                    <tr className="border-t-2 border-gray-300 font-semibold">
                                        <td colSpan={3} className="py-4 px-2 text-right text-gray-900">
                                            Totals:
                                        </td>
                                        <td className="py-4 px-2 text-right text-gray-900">
                                            ${totalDebit.toFixed(2)}
                                        </td>
                                        <td className="py-4 px-2 text-right text-gray-900">
                                            ${totalCredit.toFixed(2)}
                                        </td>
                                        <td></td>
                                    </tr>
                                    {difference > 0 && (
                                        <tr>
                                            <td colSpan={6} className="py-2 px-2">
                                                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded">
                                                    <p className="text-sm text-yellow-800 font-medium">
                                                        Out of balance by: ${difference.toFixed(2)}
                                                    </p>
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </tfoot>
                            </table>
                        </div>
                    </div>

                    {/* Messages */}
                    {error && (
                        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg">
                            <div className="flex items-center">
                                <svg
                                    className="w-5 h-5 text-red-500 mr-3"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                >
                                    <path
                                        fillRule="evenodd"
                                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                                        clipRule="evenodd"
                                    />
                                </svg>
                                <p className="text-sm text-red-700 font-medium">{error}</p>
                            </div>
                        </div>
                    )}

                    {success && (
                        <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded-lg">
                            <div className="flex items-center">
                                <svg
                                    className="w-5 h-5 text-green-500 mr-3"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                >
                                    <path
                                        fillRule="evenodd"
                                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                        clipRule="evenodd"
                                    />
                                </svg>
                                <p className="text-sm text-green-700 font-medium">
                                    Journal entry created successfully! Redirecting...
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center justify-end space-x-4">
                        <button
                            type="button"
                            onClick={() => router.back()}
                            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading || !isBalanced()}
                            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 disabled:opacity-50 disabled:cursor-not-allowed transition font-semibold shadow-lg"
                        >
                            {isLoading ? (
                                <span className="flex items-center">
                                    <svg
                                        className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                    >
                                        <circle
                                            className="opacity-25"
                                            cx="12"
                                            cy="12"
                                            r="10"
                                            stroke="currentColor"
                                            strokeWidth="4"
                                        ></circle>
                                        <path
                                            className="opacity-75"
                                            fill="currentColor"
                                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                        ></path>
                                    </svg>
                                    Saving...
                                </span>
                            ) : (
                                "Save Journal Entry"
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
