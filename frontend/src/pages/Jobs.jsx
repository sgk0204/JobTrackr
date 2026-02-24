import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import JobCard from '../components/JobCard';
import { Zap, AlertTriangle, Lightbulb } from 'lucide-react';

const Jobs = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const data = location.state;

    const [filter, setFilter] = useState('All');
    const [sortParam, setSortParam] = useState('score');

    useEffect(() => {
        if (!data || !data.jobs) {
            navigate('/dashboard');
        }
    }, [data, navigate]);

    if (!data || !data.jobs) return null;

    const { jobs, ai_tips, from_cache, total } = data;

    // Derive unique sources for filter bar
    const sources = ['All', ...new Set(jobs.map(j => j.source).filter(Boolean).map(s => {
        if (s.toLowerCase().includes('linkedin')) return 'LinkedIn';
        if (s.toLowerCase().includes('indeed')) return 'Indeed';
        if (s.toLowerCase().includes('glassdoor')) return 'Glassdoor';
        return 'Others';
    }))];

    let filteredJobs = [...jobs];

    if (filter !== 'All') {
        filteredJobs = filteredJobs.filter(j => {
            const s = j.source?.toLowerCase() || '';
            if (filter === 'LinkedIn') return s.includes('linkedin');
            if (filter === 'Indeed') return s.includes('indeed');
            if (filter === 'Glassdoor') return s.includes('glassdoor');
            return !s.includes('linkedin') && !s.includes('indeed') && !s.includes('glassdoor');
        });
    }

    if (sortParam === 'score') {
        filteredJobs.sort((a, b) => (b.ai_score || 0) - (a.ai_score || 0));
    } else if (sortParam === 'latest') {
        filteredJobs.sort((a, b) => new Date(b.posted_at) - new Date(a.posted_at));
    } else if (sortParam === 'company') {
        filteredJobs.sort((a, b) => (a.company || '').localeCompare(b.company || ''));
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

                {/* Header Section */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                            Search Results
                            {from_cache && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                    <Zap size={12} className="mr-1" /> from cache
                                </span>
                            )}
                        </h1>
                        <p className="text-gray-600 mt-1">Found {total} jobs sorted by exact match</p>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 bg-white p-2 border border-gray-200 rounded-lg shadow-sm">
                        <span className="text-sm font-medium text-gray-500 pl-2 pr-1">Sort by:</span>
                        <select
                            className="text-sm bg-gray-50 border border-gray-200 rounded-md py-1.5 px-3 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            value={sortParam}
                            onChange={(e) => setSortParam(e.target.value)}
                        >
                            <option value="score">AI Match Score</option>
                            <option value="latest">Latest First</option>
                            <option value="company">Company Name</option>
                        </select>
                    </div>
                </div>

                {/* AI Tips Section */}
                {ai_tips && ai_tips.length > 0 && (
                    <div className="mb-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                        {ai_tips.map((tip, idx) => (
                            <div key={idx} className="bg-blue-50 border border-blue-100 rounded-xl p-4 flex gap-3 shadow-sm">
                                <div className="text-2xl">{tip.icon || <Lightbulb className="text-blue-500" />}</div>
                                <p className="text-sm text-blue-900 font-medium">{tip.tip}</p>
                            </div>
                        ))}
                    </div>
                )}

                {/* Filter Bar */}
                <div className="flex gap-2 overflow-x-auto pb-4 mb-4 hide-scrollbar">
                    {sources.map(source => (
                        <button
                            key={source}
                            onClick={() => setFilter(source)}
                            className={`whitespace-nowrap px-4 py-2 rounded-full text-sm font-medium transition-colors ${filter === source ? 'bg-gray-900 text-white shadow-md' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
                        >
                            {source}
                        </button>
                    ))}
                </div>

                {/* Job Grid */}
                {filteredJobs.length === 0 ? (
                    <div className="text-center py-20 bg-white rounded-xl border border-dashed border-gray-300">
                        <AlertTriangle className="mx-auto h-12 w-12 text-gray-400 mb-3" />
                        <h3 className="text-lg font-medium text-gray-900">No jobs found</h3>
                        <p className="text-gray-500 mt-1">Try adjusting your filters or searching another role.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {filteredJobs.map((job) => (
                            <JobCard key={job.external_id || job.id} job={job} />
                        ))}
                    </div>
                )}

            </main>
        </div>
    );
};

export default Jobs;
