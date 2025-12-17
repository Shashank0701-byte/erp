"use client";

import { useState, useMemo, useEffect } from "react";
import {
    useReactTable,
    getCoreRowModel,
    getFilteredRowModel,
    getPaginationRowModel,
    getSortedRowModel,
    flexRender,
    ColumnDef,
    SortingState,
    ColumnFiltersState,
} from "@tanstack/react-table";

interface InventoryItem {
    id: string;
    sku: string;
    productName: string;
    category: string;
    quantity: number;
    reorderLevel: number;
    unitPrice: number;
    location: string;
    lastUpdated: string;
    status: "In Stock" | "Low Stock" | "Out of Stock";
}

// Mock data - replace with real API call
const generateMockData = (): InventoryItem[] => {
    const categories = ["Electronics", "Furniture", "Office Supplies", "Hardware", "Software"];
    const locations = ["Warehouse A", "Warehouse B", "Store 1", "Store 2"];
    const products = [
        "Laptop Computer", "Office Chair", "Printer Paper", "USB Cable", "Monitor",
        "Desk Lamp", "Keyboard", "Mouse", "Headphones", "Webcam",
        "Standing Desk", "Filing Cabinet", "Whiteboard", "Projector", "Router"
    ];

    return Array.from({ length: 50 }, (_, i) => {
        const quantity = Math.floor(Math.random() * 200);
        const reorderLevel = Math.floor(Math.random() * 50) + 10;

        return {
            id: `INV-${String(i + 1).padStart(4, "0")}`,
            sku: `SKU-${String(Math.floor(Math.random() * 10000)).padStart(5, "0")}`,
            productName: products[Math.floor(Math.random() * products.length)],
            category: categories[Math.floor(Math.random() * categories.length)],
            quantity,
            reorderLevel,
            unitPrice: parseFloat((Math.random() * 500 + 10).toFixed(2)),
            location: locations[Math.floor(Math.random() * locations.length)],
            lastUpdated: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
            status: quantity === 0 ? "Out of Stock" : quantity <= reorderLevel ? "Low Stock" : "In Stock",
        };
    });
};

export default function InventoryDashboard() {
    const [data, setData] = useState<InventoryItem[]>([]);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setData(generateMockData());
        setMounted(true);
    }, []);
    const [sorting, setSorting] = useState<SortingState>([]);
    const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
    const [globalFilter, setGlobalFilter] = useState("");

    const columns = useMemo<ColumnDef<InventoryItem>[]>(
        () => [
            {
                accessorKey: "id",
                header: "ID",
                cell: (info) => (
                    <span className="font-mono text-sm text-gray-900">{info.getValue() as string}</span>
                ),
            },
            {
                accessorKey: "sku",
                header: "SKU",
                cell: (info) => (
                    <span className="font-mono text-xs text-gray-600">{info.getValue() as string}</span>
                ),
            },
            {
                accessorKey: "productName",
                header: "Product Name",
                cell: (info) => (
                    <span className="font-medium text-gray-900">{info.getValue() as string}</span>
                ),
            },
            {
                accessorKey: "category",
                header: "Category",
                cell: (info) => (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {info.getValue() as string}
                    </span>
                ),
            },
            {
                accessorKey: "quantity",
                header: "Quantity",
                cell: (info) => {
                    const quantity = info.getValue() as number;
                    const reorderLevel = info.row.original.reorderLevel;
                    return (
                        <span
                            className={`font-semibold ${quantity === 0
                                ? "text-red-600"
                                : quantity <= reorderLevel
                                    ? "text-yellow-600"
                                    : "text-green-600"
                                }`}
                        >
                            {quantity}
                        </span>
                    );
                },
            },
            {
                accessorKey: "reorderLevel",
                header: "Reorder Level",
                cell: (info) => (
                    <span className="text-gray-600">{info.getValue() as number}</span>
                ),
            },
            {
                accessorKey: "unitPrice",
                header: "Unit Price",
                cell: (info) => (
                    <span className="font-medium text-gray-900">
                        ${(info.getValue() as number).toFixed(2)}
                    </span>
                ),
            },
            {
                accessorKey: "location",
                header: "Location",
                cell: (info) => (
                    <span className="text-sm text-gray-600">{info.getValue() as string}</span>
                ),
            },
            {
                accessorKey: "status",
                header: "Status",
                cell: (info) => {
                    const status = info.getValue() as string;
                    const statusColors = {
                        "In Stock": "bg-green-100 text-green-800",
                        "Low Stock": "bg-yellow-100 text-yellow-800",
                        "Out of Stock": "bg-red-100 text-red-800",
                    };
                    return (
                        <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[status as keyof typeof statusColors]
                                }`}
                        >
                            {status}
                        </span>
                    );
                },
            },
            {
                accessorKey: "lastUpdated",
                header: "Last Updated",
                cell: (info) => {
                    const date = new Date(info.getValue() as string);
                    return (
                        <span className="text-xs text-gray-500">
                            {date.toLocaleDateString()} {date.toLocaleTimeString()}
                        </span>
                    );
                },
            },
        ],
        []
    );

    const table = useReactTable({
        data,
        columns,
        state: {
            sorting,
            columnFilters,
            globalFilter,
        },
        onSortingChange: setSorting,
        onColumnFiltersChange: setColumnFilters,
        onGlobalFilterChange: setGlobalFilter,
        getCoreRowModel: getCoreRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        initialState: {
            pagination: {
                pageSize: 10,
            },
        },
    });

    const stats = useMemo(() => {
        const totalItems = data.length;
        const inStock = data.filter((item) => item.status === "In Stock").length;
        const lowStock = data.filter((item) => item.status === "Low Stock").length;
        const outOfStock = data.filter((item) => item.status === "Out of Stock").length;
        const totalValue = data.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0);

        return { totalItems, inStock, lowStock, outOfStock, totalValue };
    }, [data]);

    if (!mounted) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading inventory...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">Inventory Dashboard</h1>
                    <p className="text-gray-600 mt-2">Real-time inventory tracking and management</p>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Total Items</p>
                                <p className="text-2xl font-bold text-gray-900 mt-1">{stats.totalItems}</p>
                            </div>
                            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                                </svg>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">In Stock</p>
                                <p className="text-2xl font-bold text-green-600 mt-1">{stats.inStock}</p>
                            </div>
                            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Low Stock</p>
                                <p className="text-2xl font-bold text-yellow-600 mt-1">{stats.lowStock}</p>
                            </div>
                            <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Out of Stock</p>
                                <p className="text-2xl font-bold text-red-600 mt-1">{stats.outOfStock}</p>
                            </div>
                            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Total Value</p>
                                <p className="text-2xl font-bold text-gray-900 mt-1">
                                    ${stats.totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </p>
                            </div>
                            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Table Card */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200">
                    {/* Search and Filters */}
                    <div className="p-6 border-b border-gray-200">
                        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                            <div className="relative flex-1 max-w-md">
                                <input
                                    type="text"
                                    value={globalFilter ?? ""}
                                    onChange={(e) => setGlobalFilter(e.target.value)}
                                    placeholder="Search inventory..."
                                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition placeholder:text-gray-400"
                                />
                                <svg
                                    className="absolute left-3 top-2.5 w-5 h-5 text-gray-400"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                                    />
                                </svg>
                            </div>

                            <div className="flex items-center gap-3">
                                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium text-sm flex items-center">
                                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                                    </svg>
                                    Add Item
                                </button>
                                <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium text-sm flex items-center">
                                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                    </svg>
                                    Export
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Table */}
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50 border-b border-gray-200">
                                {table.getHeaderGroups().map((headerGroup) => (
                                    <tr key={headerGroup.id}>
                                        {headerGroup.headers.map((header) => (
                                            <th
                                                key={header.id}
                                                className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition"
                                                onClick={header.column.getToggleSortingHandler()}
                                            >
                                                <div className="flex items-center space-x-1">
                                                    <span>
                                                        {header.isPlaceholder
                                                            ? null
                                                            : flexRender(header.column.columnDef.header, header.getContext())}
                                                    </span>
                                                    {header.column.getIsSorted() && (
                                                        <span className="text-blue-600">
                                                            {header.column.getIsSorted() === "asc" ? "↑" : "↓"}
                                                        </span>
                                                    )}
                                                </div>
                                            </th>
                                        ))}
                                    </tr>
                                ))}
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {table.getRowModel().rows.map((row) => (
                                    <tr key={row.id} className="hover:bg-gray-50 transition">
                                        {row.getVisibleCells().map((cell) => (
                                            <td key={cell.id} className="px-6 py-4 whitespace-nowrap">
                                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    <div className="px-6 py-4 border-t border-gray-200">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <span className="text-sm text-gray-700">
                                    Showing{" "}
                                    <span className="font-medium">
                                        {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}
                                    </span>{" "}
                                    to{" "}
                                    <span className="font-medium">
                                        {Math.min(
                                            (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
                                            table.getFilteredRowModel().rows.length
                                        )}
                                    </span>{" "}
                                    of{" "}
                                    <span className="font-medium">{table.getFilteredRowModel().rows.length}</span> results
                                </span>
                            </div>

                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => table.setPageIndex(0)}
                                    disabled={!table.getCanPreviousPage()}
                                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
                                >
                                    First
                                </button>
                                <button
                                    onClick={() => table.previousPage()}
                                    disabled={!table.getCanPreviousPage()}
                                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
                                >
                                    Previous
                                </button>
                                <span className="px-3 py-1 text-sm text-gray-700">
                                    Page{" "}
                                    <span className="font-medium">{table.getState().pagination.pageIndex + 1}</span> of{" "}
                                    <span className="font-medium">{table.getPageCount()}</span>
                                </span>
                                <button
                                    onClick={() => table.nextPage()}
                                    disabled={!table.getCanNextPage()}
                                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
                                >
                                    Next
                                </button>
                                <button
                                    onClick={() => table.setPageIndex(table.getPageCount() - 1)}
                                    disabled={!table.getCanNextPage()}
                                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
                                >
                                    Last
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
