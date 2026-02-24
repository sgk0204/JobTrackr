import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Briefcase, LogOut } from 'lucide-react';
import { AuthContext } from '../context/AuthContext';

const Navbar = () => {
    const { user, logout } = useContext(AuthContext);
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <nav className="bg-white shadow-sm border-b border-gray-100 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex">
                        <Link to="/dashboard" className="flex-shrink-0 flex items-center gap-2">
                            <Briefcase className="h-8 w-8 text-blue-600" />
                            <span className="font-bold text-xl text-gray-900 hidden sm:block">JobTrackr</span>
                        </Link>
                    </div>
                    <div className="flex items-center gap-6">
                        <Link to="/my-jobs" className="text-gray-600 hover:text-blue-600 font-medium text-sm transition-colors">
                            My Jobs
                        </Link>

                        <div className="flex items-center gap-3 pl-6 border-l border-gray-200">
                            {user?.avatar_url ? (
                                <img className="h-8 w-8 rounded-full border border-gray-200 object-cover" src={user.avatar_url} alt="" />
                            ) : (
                                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold border border-blue-200">
                                    {user?.name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                                </div>
                            )}
                            <span className="text-sm font-medium text-gray-700 hidden md:block">
                                {user?.name || 'User'}
                            </span>
                            <button
                                onClick={handleLogout}
                                className="ml-2 p-1.5 text-gray-400 hover:text-red-500 rounded-md transition-colors"
                                title="Log out"
                            >
                                <LogOut size={18} />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
