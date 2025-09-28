import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from "../components/Navbar";


export default function AdminLayout() {

    return (
        <div className="relative min-h-screen bg-bg-primary">
            <Navbar/>
            <main>
                <div>
                    <Outlet />
                </div>
            </main>
        </div>
    );
}