import React from "react";
import { Outlet } from "react-router-dom";
import Navbar from "../components/Navbar";
import NotificationPopup from "../components/NotificationPopup";

export default function AppLayout() {
    return (
            <div className="relative min-h-screen bg-[linear-gradient(135deg,var(--bg-secondary)_0%,var(--bg-tertiary)_100%)] bg-fixed">
                <Navbar />

                <NotificationPopup />

                <main>
                    <div>
                        <Outlet />
                    </div>
                </main>
            </div>
    );
}
