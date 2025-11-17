import React, {useEffect} from 'react';
import {
    Play,
    Users,
    Settings,
    BarChart3,
    LogOut,
    User,
    Gamepad2
} from 'lucide-react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLogout } from '../hooks/useLogout';
import {applyTheme} from "../contexts/ThemeProvider";

const Navbar = ({ children }) => {
    const { user, loading } = useAuth();
    const logout = useLogout();
    const location = useLocation();
    const { pathname } = location;

    useEffect(() => {
        if (!loading && user) {
            if (user?.settings?.theme) {
                applyTheme(user.settings.theme)
            }
        }
    }, [user, loading]);

    const navigation = [
        { path: '/', icon: Play, label: 'Game' },
        { path: '/game',icon: Play, label: 'Multi' },
        { path: '/friends', icon: Users, label: 'Friends' },
        { path: '/stats', icon: BarChart3, label: 'Statistics' },
        { path: '/settings', icon: Settings, label: 'Settings' },
    ];

    return (
        <header className="bg-bg-secondary border-b-2 border-border-primary sticky top-0 z-50">
            <div className="max-w-6xl mx-auto px-5 flex flex-col md:flex-row items-center justify-between h-auto md:h-[70px] gap-4 py-4 md:py-0">

                {/* Logo */}
                <div  className="flex gap-4">
                    <div className="flex items-center gap-3 text-accent-primary">
                        <Gamepad2 size={32} />
                        <h1 className="text-2xl font-bold">Minesweeper</h1>
                    </div>
                    {/* Navigation */}
                    <nav className="flex gap-2 justify-center w-full md:w-auto order-3 md:order-none">
                        {navigation.map(({ path, icon: Icon, label }) => (
                            <NavLink
                                key={path}
                                to={path}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition
                    ${
                                    pathname === path
                                        ? 'bg-accent-primary text-bg-secondary'
                                        : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
                                }
                  `}
                            >
                                <Icon size={20} />
                                <span className="hidden md:inline">{label}</span>
                            </NavLink>
                        ))}
                    </nav>
                </div>

                {/* User Menu */}
                <div className="flex items-center gap-4 order-2 md:order-none">
                    {!loading && user ? (
                        <>
                            {/* User info */}
                            <div className="flex items-center gap-2 text-text-primary font-medium">
                                <img
                                    src={user.avatar_url || "/avatar.svg"}
                                    alt="avatar"
                                    className="w-10 h-10 rounded-full bg-white border-2 border-border-primary object-cover"
                                />
                                <span>{user.nickname || user.username}</span>
                            </div>

                            {/* Logout button */}
                            <button
                                className="flex items-center gap-2 px-4 py-2 text-text-secondary border border-border-primary rounded-lg bg-bg-tertiary hover:bg-bg-primary transition"
                                onClick={logout}
                            >
                                <LogOut size={16} />
                                Logout
                            </button>
                        </>
                    ) : (
                        <span className={`gap-2`}>


                        <NavLink
                            to="/register"
                            className="px-4 py-2 mr-2 rounded-lg bg-accent-primary text-white font-semibold hover:bg-accent-secondary transition"
                        >
                            Register
                        </NavLink>

                        <NavLink
                            to="/login"
                            className="px-4 py-2 rounded-lg bg-accent-primary text-white font-semibold hover:bg-accent-secondary transition"
                        >
                            Login
                        </NavLink>
                        </span>
                    )}
                </div>
            </div>
        </header>
    );
};

export default Navbar;
