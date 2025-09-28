import React from 'react';
import {
    Play,
    Users,
    Settings,
    BarChart3,
    LogOut,
    User,
    Gamepad2
} from 'lucide-react';


const Layout = ({ children }) => {
    // PLACEHOLDER
    const user = { username: 'PlaceholderUser' };

    // PLACEHOLDER
    const logout = () => {
        alert('Placeholder logout action');
    };

    // PLACEHOLDER
    const currentPath = '/';

    // PLACEHOLDER
    const navigation = [
        { path: '/', icon: Play, label: 'Game' },
        { path: '/friends', icon: Users, label: 'Friends' },
        { path: '/stats', icon: BarChart3, label: 'Statistics' },
        { path: '/settings', icon: Settings, label: 'Settings' },
    ];

    return (
        <header className="bg-bg-secondary border-b-2 border-border-primary sticky top-0 z-50">
            <div className="max-w-6xl mx-auto px-5 flex flex-col md:flex-row items-center justify-between h-auto md:h-[70px] gap-4 py-4 md:py-0">

                {/* Logo */}
                <div className="flex items-center gap-3 text-accent-primary">
                    <Gamepad2 size={32} />
                    <h1 className="text-2xl font-bold">Minesweeper Pro</h1>
                </div>

                {/* Navigation - <button> jako placeholdery zamiast <Link> */}
                <nav className="flex gap-2 justify-center w-full md:w-auto order-3 md:order-none">
                    {navigation.map(({ path, icon: Icon, label }) => (
                        <button
                            key={path}
                            onClick={() => alert(`Navigate to ${path}`)} // PLACEHOLDER akcji zamiast routera
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition
              ${
                                currentPath === path
                                    ? 'bg-accent-primary text-bg-secondary'
                                    : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
                            }`}
                        >
                            <Icon size={20} />
                            <span className="hidden md:inline">{label}</span>
                        </button>
                    ))}
                </nav>

                {/* User Menu */}
                <div className="flex items-center gap-4 order-2 md:order-none">
                    {/* User info */}
                    <div className="flex items-center gap-2 text-text-primary font-medium">
                        <User size={20} />
                        <span>{user?.username || 'Guest'}</span>
                    </div>

                    {/* Logout button */}
                    <button
                        className="flex items-center gap-2 px-4 py-2 text-text-secondary border-1 border-border-primary rounded-lg bg-bg-tertiary hover:bg-bg-primary transition"
                        onClick={logout}
                    >
                        <LogOut size={16} />
                        Logout
                    </button>
                </div>
            </div>
        </header>
    );
};

export default Layout;
