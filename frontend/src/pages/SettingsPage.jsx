import React, { useState } from "react";
import { applyTheme } from "../contexts/ThemeProvider";

export default function SettingsPage() {
    // Placeholdery
    const [username, setUsername] = useState("Player123");
    const [email, setEmail] = useState("player@example.com");
    const [theme, setTheme] = useState("system");
    const [avatar, setAvatar] = useState(null);

    const handleAvatarChange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Optional: validate file size (2MB max)
        const maxSizeMB = 2;
        if (file.size / 1024 / 1024 > maxSizeMB) {
            alert(`File is too large. Max size is ${maxSizeMB}MB.`);
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("api/avatar", {
                method: "POST",
                body: formData,
                credentials: "include",
            });

            if (!response.ok) {
                console.log(response);
                const errorData = await response.json();
                throw new Error(errorData.detail || "Failed to upload avatar.");
            }

            const data = await response.json();
            setAvatar(data.avatar_url);
        } catch (err) {
            console.error(err);
            alert(err.message);
        }
    };


    const handleSaveProfile = (e) => {
        e.preventDefault();
        alert("Zmieniono dane użytkownika (placeholder)");
    };

    const handleChangePassword = (e) => {
        e.preventDefault();
        alert("Zmieniono hasło (placeholder)");
    };
    //koniec placeholderow

    const handleThemeChange = (newTheme) => {
        setTheme(newTheme);
        applyTheme(newTheme);
    };


    return (
        <div className="max-w-3xl mx-auto p-6 flex flex-col gap-6 text-text-primary">
            <h1 className="text-2xl font-bold mb-2 text-text-primary">
                Account Settings
            </h1>
            <p className="text-text-secondary mb-4">
                Manage your profile, password, avatar, and appearance preferences.
            </p>

            {/* Avatar */}
            <div className="bg-bg-secondary border border-border-primary rounded-xl p-6 flex flex-col md:flex-row items-center gap-6">
                <div className="flex flex-col items-center">
                    <div className="w-24 h-24 rounded-full bg-bg-tertiary overflow-hidden flex items-center justify-center">
                        {avatar ? (
                            <img src={avatar} alt="Avatar" className="w-full h-full object-cover" />
                        ) : (
                            <span className="text-3xl font-bold text-accent-primary">
                {username.charAt(0).toUpperCase()}
              </span>
                        )}
                    </div>
                    <label className="mt-3 cursor-pointer text-accent-primary hover:underline">
                        Change Avatar
                        <input
                            type="file"
                            accept="image/*"
                            onChange={handleAvatarChange}
                            className="hidden"
                        />
                    </label>
                </div>
                <div className="flex-1 text-text-secondary">
                    <p className="text-sm">
                        Upload a square image (recommended 400×400px). Max 2MB.
                    </p>
                </div>
            </div>

            {/* Username + Email */}
            <form
                onSubmit={handleSaveProfile}
                className="bg-bg-secondary border border-border-primary rounded-xl p-6 flex flex-col gap-4"
            >
                <h2 className="text-lg font-semibold text-text-primary">Profile Info</h2>

                <div className="flex flex-col gap-1">
                    <label className="text-sm text-text-secondary">Username</label>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="px-3 py-2 bg-bg-tertiary border border-border-primary rounded-lg text-text-primary placeholder-text-secondary"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-sm text-text-secondary">Email</label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="px-3 py-2 bg-bg-tertiary border border-border-primary rounded-lg text-text-primary placeholder-text-secondary"
                    />
                </div>

                <button
                    type="submit"
                    className="self-start mt-2 px-4 py-2 bg-accent-primary text-white rounded-lg hover:opacity-90"
                >
                    Save Changes
                </button>
            </form>

            {/* Password Change */}
            <form
                onSubmit={handleChangePassword}
                className="bg-bg-secondary border border-border-primary rounded-xl p-6 flex flex-col gap-4"
            >
                <h2 className="text-lg font-semibold text-text-primary">Change Password</h2>

                <div className="flex flex-col gap-1">
                    <label className="text-sm text-text-secondary">Current Password</label>
                    <input
                        type="password"
                        placeholder="Enter current password"
                        className="px-3 py-2 bg-bg-tertiary border border-border-primary rounded-lg text-text-primary placeholder-text-secondary"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-sm text-text-secondary">New Password</label>
                    <input
                        type="password"
                        placeholder="Enter new password"
                        className="px-3 py-2 bg-bg-tertiary border border-border-primary rounded-lg text-text-primary placeholder-text-secondary"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-sm text-text-secondary">Confirm New Password</label>
                    <input
                        type="password"
                        placeholder="Repeat new password"
                        className="px-3 py-2 bg-bg-tertiary border border-border-primary rounded-lg text-text-primary placeholder-text-secondary"
                    />
                </div>

                <button
                    type="submit"
                    className="self-start mt-2 px-4 py-2 bg-accent-primary text-white rounded-lg hover:opacity-90"
                >
                    Update Password
                </button>
            </form>

            {/* Theme Selection */}
            <div className="bg-bg-secondary border border-border-primary rounded-xl p-6 flex flex-col gap-4">
                <h2 className="text-lg font-semibold text-text-primary">Theme</h2>

                <div className="flex gap-4">
                    {["light", "dark", "system"].map((option) => (
                        <button
                            key={option}
                            type="button"
                            onClick={() => handleThemeChange(option)}
                            className={`px-4 py-2 rounded-lg border border-border-primary transition ${
                                theme === option
                                    ? "bg-accent-primary text-white"
                                    : "bg-bg-tertiary text-text-secondary hover:text-text-primary"
                            }`}
                        >
                            {option.charAt(0).toUpperCase() + option.slice(1)}
                        </button>
                    ))}
                </div>

                <p className="text-sm text-text-secondary">
                </p>
            </div>
        </div>
    );
}
