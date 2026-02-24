import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Search, Bot, Briefcase, CheckCircle, Clock, XCircle } from 'lucide-react';
import Navbar from '../components/Navbar';
import api from '../services/api';

const Dashboard = () => {
    const [role, setRole] = useState('');
    const [experience, setExperience] = useState('0');
    const [isSearching, setIsSearching] = useState(false);
    const [loadingPhase, setLoadingPhase] = useState(0);
    const [stats, setStats] = useState({ applied: 0, inprocess: 0, hired: 0 });
    const navigate = useNavigate();

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const res = await api.get('/jobs/my-jobs?filter=all');
                setStats(res.data.summary);
            } catch (error) {
                console.error('Failed to fetch stats', error);
            }
        };
        fetchStats();
    }, []);

    const loadingMessages = [
        "Initializing AI Agent...",
        "Scanning LinkedIn, Indeed, Glassdoor...",
        "🤖 Gemini AI is ranking results...",
        "Finalizing best matches..."
    ];

    useEffect(() => {
        let interval;
        if (isSearching) {
            interval = setInterval(() => {
                setLoadingPhase((prev) => (prev < loadingMessages.length - 1 ? prev + 1 : prev));
            }, 2500);
        }
        return () => clearInterval(interval);
    }, [isSearching]);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!role.trim()) {
            toast.error('Please enter a role');
            return;
        }

        setIsSearching(true);
        setLoadingPhase(0);

        try {
            const res = await api.get(`/jobs/search`, {
                params: { role, experience: parseInt(experience) }
            });

            toast.success(`Found ${res.data.total} jobs!`);
            navigate('/jobs', { state: res.data });
        } catch (error) {
            console.error(error);
            toast.error('Search failed. Please try again.');
        } finally {
            setIsSearching(false);
        }
    };

    if (isSearching) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center">
                <Bot className="h-16 w-16 text-blue-600 animate-bounce mb-6" />
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                    {loadingMessages[loadingPhase]}
                </h2>
                <div className="w-64 bg-gray-200 rounded-full h-2.5 mt-4">
                    <div
                        className="bg-blue-600 h-2.5 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${((loadingPhase + 1) / loadingMessages.length) * 100}%` }}
                    ></div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">

                {/* Search Hero Section */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mb-10">
                    <div className="bg-gradient-to-r from-blue-600 to-indigo-700 px-8 py-12 text-center">
                        <h1 className="text-4xl font-extrabold text-white mb-4 tracking-tight">
                            Find your next role with AI
                        </h1>

                    </div>

                    <div className="px-8 py-8">
                        <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4 max-w-4xl mx-auto">
                            <div className="flex-grow">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Job Role</label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Search className="h-5 w-5 text-gray-400" />
                                    </div>
                                    <input
                                        type="text"
                                        required
                                        placeholder="e.g. React Developer, Data Scientist"
                                        className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-md"
                                        value={role}
                                        onChange={(e) => setRole(e.target.value)}
                                        list="role-suggestions"
                                    />
                                    <datalist id="role-suggestions">
                                        <option value="Software Engineer" />
                                        <option value="Frontend Developer" />
                                        <option value="Backend Developer" />
                                        <option value="Full Stack Developer" />
                                        <option value="Data Analyst" />
                                        <option value="Product Manager" />
                                    </datalist>
                                </div>
                            </div>

                            <div className="w-full md:w-48">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Experience</label>
                                <select
                                    value={experience}
                                    onChange={(e) => setExperience(e.target.value)}
                                    className="block w-full px-3 py-3 bg-white border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-md"
                                >
                                    <option value="0">Fresher / 0 years</option>
                                    <option value="1">1 year</option>
                                    <option value="2">2 years</option>
                                    <option value="3">3 years</option>
                                    <option value="5">5+ years</option>
                                    <option value="10">10+ years</option>
                                </select>
                            </div>

                            <div className="flex items-end">
                                <button
                                    type="submit"
                                    className="w-full md:w-auto px-8 py-3 border border-transparent text-base font-medium rounded-xl text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 shadow-sm transition-all hover:shadow-md"
                                >
                                    Search Jobs
                                </button>
                            </div>
                        </form>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="mb-4">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">Your Application Overview</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <StatCard
                            title="Total Applied"
                            value={stats.applied || 0}
                            icon={<Briefcase className="h-6 w-6 text-blue-600" />}
                            color="bg-blue-50 border-blue-100"
                        />
                        <StatCard
                            title="In Process"
                            value={stats.inprocess || 0}
                            icon={<Clock className="h-6 w-6 text-yellow-600" />}
                            color="bg-yellow-50 border-yellow-100"
                        />
                        <StatCard
                            title="Hired"
                            value={stats.hired || 0}
                            icon={<CheckCircle className="h-6 w-6 text-green-600" />}
                            color="bg-green-50 border-green-100"
                        />
                    </div>
                </div>

            </main>
        </div>
    );
};

const StatCard = ({ title, value, icon, color }) => (
    <div className={`rounded-xl p-6 border ${color} shadow-sm cursor-pointer hover:shadow-md transition-shadow`} onClick={() => window.location.href = '/my-jobs'}>
        <div className="flex items-center justify-between">
            <div>
                <p className="text-sm font-medium text-gray-500 truncate">{title}</p>
                <p className="mt-2 text-3xl font-extrabold text-gray-900">{value}</p>
            </div>
            <div className={`p-3 rounded-full bg-white bg-opacity-60`}>
                {icon}
            </div>
        </div>
    </div>
);

export default Dashboard;
