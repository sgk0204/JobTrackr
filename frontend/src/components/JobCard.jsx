import React, { useState } from 'react';
import { Bookmark, Send, ExternalLink, Bot, MapPin, Building, Banknote, Clock } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';

const JobCard = ({ job, onApply, onSave }) => {
    const [isApplying, setIsApplying] = useState(false);
    const [isSaving, setIsSaving] = useState(false);



    const getSourceBadgeColor = (source) => {
        const s = source?.toLowerCase() || '';
        if (s.includes('linkedin')) return 'bg-blue-100 text-blue-700';
        if (s.includes('indeed')) return 'bg-purple-100 text-purple-700';
        if (s.includes('glassdoor')) return 'bg-green-100 text-green-700';
        return 'bg-gray-100 text-gray-700';
    };

    const handleApply = async () => {
        setIsApplying(true);
        try {
            await api.post(`/jobs/apply/${job.id || job.external_id}`);
            toast.success('Application tracked!');
            if (onApply) onApply(job);
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to track application');
        } finally {
            setIsApplying(false);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await api.post(`/jobs/save/${job.id || job.external_id}`);
            toast.success('Job saved!');
            if (onSave) onSave(job);
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to save job');
        } finally {
            setIsSaving(false);
        }
    };

    const formatTime = (isoString) => {
        if (!isoString) return 'recently';
        const date = new Date(isoString);
        const diff = Math.floor((new Date() - date) / 1000 / 60 / 60);
        if (diff < 1) return 'Just now';
        if (diff < 24) return `${diff} hours ago`;
        return `${Math.floor(diff / 24)} days ago`;
    };

    return (
        <div
            className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow duration-200 flex flex-col h-full cursor-pointer hover:border-indigo-300"
            onClick={(e) => {
                if (e.target.closest('button') || e.target.closest('a') || e.target.tagName.toLowerCase() === 'h3') return;
                if (job.apply_url) window.open(job.apply_url, '_blank', 'noopener,noreferrer');
            }}
        >
            <div className="p-5 flex-grow">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <h3
                            className="text-lg font-bold text-gray-900 line-clamp-1 hover:text-blue-600 cursor-pointer"
                            onClick={(e) => {
                                e.stopPropagation();
                                if (job.apply_url) window.open(job.apply_url, '_blank', 'noopener,noreferrer');
                            }}
                        >
                            {job.title}
                        </h3>
                        <div className="flex items-center text-sm text-gray-600 mt-1">
                            <Building size={16} className="mr-1.5 text-gray-400" />
                            <span className="font-medium mr-3">{job.company}</span>
                        </div>
                    </div>
                </div>

                <div className="flex flex-wrap gap-2 mb-4">
                    {job.location && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-gray-700">
                            <MapPin size={12} className="mr-1" />
                            {job.location}
                        </span>
                    )}
                    {job.salary_range && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-green-50 text-green-700 border border-green-100">
                            <Banknote size={12} className="mr-1" />
                            {job.salary_range}
                        </span>
                    )}
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium ${getSourceBadgeColor(job.source)}`}>
                        {job.source || 'Multiple'}
                    </span>
                </div>

                <p className="text-sm text-gray-600 line-clamp-3 mb-4">
                    {job.description || 'No description available for this job posting. Click apply to read more on the company website.'}
                </p>
            </div >

            <div className="bg-gray-50 px-5 py-4 border-t border-gray-100 flex items-center justify-between">
                <div className="flex items-center text-xs text-gray-500">
                    <Clock size={12} className="mr-1" />
                    {formatTime(job.posted_at)}
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={handleSave}
                        disabled={isSaving}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors border border-transparent shadow-sm hover:border-blue-200"
                        title="Save for later"
                    >
                        <Bookmark size={18} />
                    </button>

                    <button
                        onClick={handleApply}
                        disabled={isApplying}
                        className="px-3 py-1.5 flex items-center text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors"
                    >
                        Track <Send size={14} className="ml-1.5" />
                    </button>

                    {job.apply_url && (
                        <a
                            href={job.apply_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-3 py-1.5 flex items-center text-sm font-medium text-blue-700 bg-blue-100 hover:bg-blue-200 rounded-lg transition-colors border border-blue-200"
                        >
                            Apply <ExternalLink size={14} className="ml-1.5" />
                        </a>
                    )}
                </div>
            </div>
        </div >
    );
};

export default JobCard;
