import React, { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { Gamepad2, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import './styles/auth.css';

const LoginPage = () => {
    const { user, setUser } = useAuth();
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        username: '',
        password: '',
    });
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    if (user) {
        return <Navigate to="/" replace />;
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const body = new URLSearchParams();
            body.append('username', formData.username);
            body.append('password', formData.password);

            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    Accept: 'application/json',
                },
                body,
                credentials: 'include',
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Login failed');
            }

            const meRes = await fetch('/api/auth/me', { credentials: 'include' });
            if (meRes.ok) {
                const meData = await meRes.json();
                setUser(meData);
            }

            navigate('/');
        } catch (err) {
            setError(err.message || 'Unexpected error');
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) =>
        setFormData({ ...formData, [e.target.name]: e.target.value });

    return (
        <div className="min-h-screen flex items-center justify-center bg-[linear-gradient(135deg,var(--bg-primary)_0%,var(--bg-tertiary)_100%)] p-5">
            <div className="w-full max-w-md">
                <div className="auth-card bg-bg-secondary border-2 border-border-primary rounded-2xl p-10 shadow-[0_10px_25px_rgba(0,0,0,0.1)] animate-slideUp">
                    <div className="text-center mb-8">
                        <Gamepad2 size={48} className="mx-auto mb-4 text-accent-primary" />
                        <h1 className="text-[28px] font-bold text-text-primary mb-2">
                            Welcome Back
                        </h1>
                        <p className="text-[16px] text-text-secondary">
                            Sign in to continue your Minesweeper journey
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
                        {error && (
                            <div className="flex items-center gap-2 p-3 bg-error text-white rounded-lg text-sm font-medium">
                                <AlertCircle size={16} />
                                {error}
                            </div>
                        )}

                        <div className="flex flex-col gap-2">
                            <label
                                htmlFor="username"
                                className="text-[14px] font-semibold text-text-primary"
                            >
                                Username or Email
                            </label>
                            <input
                                type="text"
                                id="username"
                                name="username"
                                value={formData.username}
                                onChange={handleChange}
                                required
                                placeholder="Enter your username or email"
                                className="px-3 py-2 rounded-md border border-border-primary bg-cell-revealed text-text-primary placeholder:text-text-secondary focus:outline-none focus:ring-2 focus:ring-accent-primary"
                            />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label
                                htmlFor="password"
                                className="text-[14px] font-semibold text-text-primary"
                            >
                                Password
                            </label>
                            <div className="relative">
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    id="password"
                                    name="password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    required
                                    placeholder="Enter your password"
                                    className="w-full px-3 py-2 rounded-md border border-border-primary bg-cell-revealed text-text-primary placeholder:text-text-secondary focus:outline-none focus:ring-2 focus:ring-accent-primary"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary p-1 rounded transition-colors"
                                >
                                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="mt-2 py-3 rounded-lg font-semibold text-[16px] bg-accent-primary text-white hover:bg-accent-secondary transition disabled:opacity-60 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Signing In...' : 'Sign In'}
                        </button>
                    </form>

                    <div className="text-center mt-8 pt-5 border-t border-border-primary">
                        <p className="text-text-secondary">
                            Don't have an account?{' '}
                            <Link
                                to="/register"
                                className="text-accent-primary font-semibold hover:text-accent-secondary transition"
                            >
                                Sign up here
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
