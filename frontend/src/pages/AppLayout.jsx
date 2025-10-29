import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from "../components/Navbar";


export default function AppLayout() {

    return (
        <div className="relative min-h-screen bg-[linear-gradient(135deg,var(--bg-secondary)_0%,var(--bg-tertiary)_100%)] bg-fixed">
            <Navbar/>
            <main>
                <div>
                    <Outlet />
                </div>
            </main>
        </div>
    );
}