import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import Navbar from '../components/Navbar';
import api from '../services/api';
import toast from 'react-hot-toast';
import { Building, Bookmark, Trash2, Settings, LayoutList, LayoutGrid } from 'lucide-react';

const COLUMNS = [
    { id: 'applied', title: 'Applied', color: 'border-blue-400', bg: 'bg-blue-50' },
    { id: 'inprocess', title: 'In Process', color: 'border-yellow-400', bg: 'bg-yellow-50' },
    { id: 'rejected', title: 'Rejected', color: 'border-red-400', bg: 'bg-red-50' },
    { id: 'hired', title: 'Hired', color: 'border-green-400', bg: 'bg-green-50' }
];

const MyJobs = () => {
    const [jobs, setJobs] = useState([]);
    const [summary, setSummary] = useState({});
    const [viewMode, setViewMode] = useState('kanban'); // 'list' | 'kanban'
    const [isLoading, setIsLoading] = useState(true);

    const fetchMyJobs = async () => {
        setIsLoading(true);
        try {
            const res = await api.get('/jobs/my-jobs?filter=all');
            setJobs(res.data.jobs);
            setSummary(res.data.summary);
        } catch (error) {
            toast.error('Failed to load my jobs');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchMyJobs();
    }, []);

    const handleStatusChange = async (jobId, newStatus) => {
        try {
            await api.patch(`/jobs/apply/${jobId}/status`, { status: newStatus });
            setJobs(jobs.map(j => j.id === jobId ? { ...j, status: newStatus } : j));
            toast.success('Status updated');
            fetchMyJobs(); // Re-fetch for updated summary
        } catch {
            toast.error('Gosh, status update failed');
            fetchMyJobs(); // Revert
        }
    };

    const handleDelete = async (jobId, isSavedOnly) => {
        try {
            if (isSavedOnly) {
                await api.delete(`/jobs/save/${jobId}`);
            } else {
                await api.delete(`/jobs/apply/${jobId}`);
            }
            setJobs(jobs.filter(j => j.id !== jobId));
            toast.success('Job removed');
            fetchMyJobs();
        } catch {
            toast.error('Failed to remove job');
        }
    };

    const onDragEnd = (result) => {
        const { destination, source, draggableId } = result;
        if (!destination) return;
        if (destination.droppableId === source.droppableId) return;

        handleStatusChange(draggableId, destination.droppableId);
    };

    const getJobsByStatus = (status) => jobs.filter(j => j.status === status);
    const getSavedOnlyJobs = () => jobs.filter(j => !j.status && j.saved_at);

    if (isLoading) {
        return <div className="min-h-screen bg-gray-50 pt-20 text-center">Loading jobs...</div>;
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

                <div className="flex flex-col sm:flex-row justify-between items-center mb-8 gap-4">
                    <h1 className="text-2xl font-bold text-gray-900">Job Applications Tracker</h1>

                    <div className="flex items-center gap-2 p-1 bg-white border border-gray-200 rounded-lg shadow-sm">
                        <button
                            className={`p-2 rounded-md ${viewMode === 'list' ? 'bg-gray-100 text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                            onClick={() => setViewMode('list')}
                            title="List View"
                        >
                            <LayoutList size={20} />
                        </button>
                        <button
                            className={`p-2 rounded-md ${viewMode === 'kanban' ? 'bg-gray-100 text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                            onClick={() => setViewMode('kanban')}
                            title="Kanban View"
                        >
                            <LayoutGrid size={20} />
                        </button>
                    </div>
                </div>

                {viewMode === 'kanban' ? (
                    <DragDropContext onDragEnd={onDragEnd}>
                        <div className="flex flex-nowrap overflow-x-auto gap-6 pb-4 hide-scrollbar">
                            {COLUMNS.map((col) => {
                                const columnJobs = getJobsByStatus(col.id);
                                return (
                                    <div key={col.id} className="min-w-[300px] flex-1 bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col items-stretch max-w-sm h-[calc(100vh-250px)]">
                                        <div className={`px-4 py-3 border-b-2 ${col.color} flex justify-between items-center bg-gray-50 rounded-t-xl`}>
                                            <h3 className="font-bold text-gray-800 uppercase text-xs tracking-wider">{col.title}</h3>
                                            <span className="bg-white text-gray-600 px-2 py-0.5 rounded-full text-xs font-bold shadow-sm border border-gray-200">
                                                {columnJobs.length}
                                            </span>
                                        </div>

                                        <Droppable droppableId={col.id}>
                                            {(provided, snapshot) => (
                                                <div
                                                    ref={provided.innerRef}
                                                    {...provided.droppableProps}
                                                    className={`flex-1 p-3 overflow-y-auto transition-colors ${snapshot.isDraggingOver ? col.bg : ''}`}
                                                >
                                                    {columnJobs.map((job, index) => (
                                                        <Draggable key={job.id} draggableId={job.id} index={index}>
                                                            {(provided, snapshot) => (
                                                                <div
                                                                    ref={provided.innerRef}
                                                                    {...provided.draggableProps}
                                                                    {...provided.dragHandleProps}
                                                                    className={`mb-3 bg-white p-4 rounded-lg shadow-sm border ${snapshot.isDragging ? 'border-primary ring-2 ring-blue-500 ring-opacity-50' : 'border-gray-200'} hover:border-blue-300 transition-colors cursor-pointer`}
                                                                    onClick={(e) => {
                                                                        if (e.target.closest('button') || e.target.closest('a')) return;
                                                                        if (job.apply_url) window.open(job.apply_url, '_blank', 'noopener,noreferrer');
                                                                    }}
                                                                >
                                                                    <h4
                                                                        className="font-semibold text-gray-900 text-sm mb-1 hover:text-blue-600 cursor-pointer"
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            if (job.apply_url) window.open(job.apply_url, '_blank', 'noopener,noreferrer');
                                                                        }}
                                                                    >
                                                                        {job.title}
                                                                    </h4>
                                                                    <div className="flex items-center text-xs text-gray-600 mb-3">
                                                                        <Building size={12} className="mr-1" /> {job.company}
                                                                    </div>
                                                                    <div className="flex justify-between items-center">
                                                                        <span className="text-[10px] text-gray-400 font-medium">
                                                                            Applied: {new Date(job.applied_at).toLocaleDateString()}
                                                                        </span>
                                                                        <button
                                                                            onClick={(e) => { e.stopPropagation(); handleDelete(job.id, false); }}
                                                                            className="text-gray-400 hover:text-red-500"
                                                                        >
                                                                            <Trash2 size={14} />
                                                                        </button>
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </Draggable>
                                                    ))}
                                                    {provided.placeholder}
                                                </div>
                                            )}
                                        </Droppable>
                                    </div>
                                );
                            })}
                        </div>
                    </DragDropContext>
                ) : (
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Job</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {jobs.filter(j => j.status).map(job => (
                                    <tr key={job.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                            {job.apply_url ? <a href={job.apply_url} target="_blank" rel="noreferrer" className="hover:text-blue-600 hover:underline">{job.title}</a> : job.title}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{job.company}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(job.applied_at).toLocaleDateString()}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            <select
                                                value={job.status}
                                                onChange={(e) => handleStatusChange(job.id, e.target.value)}
                                                className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2"
                                            >
                                                {COLUMNS.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}
                                            </select>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <button onClick={() => handleDelete(job.id, false)} className="text-red-500 hover:text-red-700">Delete</button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Saved Jobs List */}
                {getSavedOnlyJobs().length > 0 && (
                    <div className="mt-12">
                        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                            <Bookmark className="mr-2 text-blue-600" /> Saved Jobs
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {getSavedOnlyJobs().map(job => (
                                <div
                                    key={job.id}
                                    className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm cursor-pointer hover:border-indigo-300 transition-colors"
                                    onClick={(e) => {
                                        if (e.target.closest('button') || e.target.closest('a')) return;
                                        if (job.apply_url) window.open(job.apply_url, '_blank', 'noopener,noreferrer');
                                    }}
                                >
                                    <h4
                                        className="font-bold text-gray-900 line-clamp-1 hover:text-blue-600 cursor-pointer"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            if (job.apply_url) window.open(job.apply_url, '_blank', 'noopener,noreferrer');
                                        }}
                                    >
                                        {job.title}
                                    </h4>
                                    <p className="text-gray-500 text-sm mt-1 mb-4 flex items-center"><Building size={14} className="mr-1" />{job.company}</p>
                                    <div className="flex justify-between items-center mt-auto border-t border-gray-100 pt-3">
                                        <button
                                            onClick={() => handleStatusChange(job.id, 'applied')}
                                            className="text-sm font-medium text-blue-600 hover:text-blue-800"
                                        >
                                            Mark as Applied
                                        </button>
                                        <button onClick={() => handleDelete(job.id, true)} className="text-gray-400 hover:text-red-500">
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

            </main>
        </div>
    );
};

export default MyJobs;
