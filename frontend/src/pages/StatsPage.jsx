import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { ChevronLeft, ChevronRight, Users, Globe, Lock } from "lucide-react";

export default function StatsPage() {
    const { user, loading: authLoading } = useAuth();

    const [rankingType, setRankingType] = useState("users"); // "users" | "gameplays"
    const [scope, setScope] = useState("global"); // "global" | "friends"
    const [compareBy, setCompareBy] = useState("win_rate");
    const [difficultyLevelId, setDifficultyLevelId] = useState(null); // TODO: dynamic later
    const [stats, setStats] = useState([]);
    const [loading, setLoading] = useState(false);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const loggedIn = !!user && !authLoading;

    async function fetchStats() {
        if (scope === "friends" && !loggedIn) {
            setStats([]);
            return;
        }

        setLoading(true);
        try {
            const diffId = difficultyLevelId || "00000000-0000-0000-0000-000000000000";
            let url = `/api/stats/${rankingType}/${scope}?difficulty_level_id=${diffId}&page=${page}&size=10`;

            if (rankingType === "users") url += `&compare_by=${compareBy}`;

            const res = await fetch(url, {
                method: "GET",
                credentials: "include",
            });

            if (!res.ok) throw new Error("Failed to load stats");

            const data = await res.json();
            setStats(data.items || []);
            setTotalPages(data.pages || 1);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        if (!authLoading) {
            fetchStats();
        }
    }, [rankingType, scope, compareBy, page, authLoading]);

    const tabs = [
        { id: "users", label: "Users Ranking" },
        { id: "gameplays", label: "Gameplays Ranking" },
    ];

    return (
        <div className="max-w-4xl mx-auto p-6">
            <div className="text-center mb-8">
                <h1 className="text-3xl font-bold text-text-primary mb-2">Statistics</h1>
                <p className="text-text-secondary">
                    Compare your performance with players around the world or your friends.
                </p>
            </div>

            {/* Tabs */}
            <div className="flex justify-center gap-3 mb-6 bg-bg-tertiary p-2 rounded-xl">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => {
                            setRankingType(tab.id);
                            setPage(1);
                        }}
                        className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                            rankingType === tab.id
                                ? "bg-bg-secondary text-accent-primary"
                                : "text-text-secondary hover:text-text-primary"
                        }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Filters */}
            <div className="flex flex-wrap justify-center gap-4 mb-6">
                <div className="flex gap-2">
                    <button
                        onClick={() => {
                            setScope("global");
                            setPage(1);
                        }}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${
                            scope === "global"
                                ? "bg-bg-secondary border-accent-primary text-accent-primary"
                                : "border-border-primary text-text-secondary hover:text-text-primary"
                        }`}
                    >
                        <Globe size={18} /> Global
                    </button>

                    <button
                        onClick={() => {
                            if (!loggedIn) return; // prevent toggle if not logged in
                            setScope("friends");
                            setPage(1);
                        }}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${
                            scope === "friends"
                                ? "bg-bg-secondary border-accent-primary text-accent-primary"
                                : "border-border-primary text-text-secondary hover:text-text-primary"
                        } ${!loggedIn ? "opacity-50" : ""}`}
                    >
                        <Users size={18} /> Friends
                        {!loggedIn && <Lock size={14} />}
                    </button>
                </div>

                {rankingType === "users" && (
                    <select
                        className="bg-bg-secondary text-text-primary border border-border-primary rounded-lg px-3 py-2"
                        value={compareBy}
                        onChange={(e) => setCompareBy(e.target.value)}
                    >
                        <option value="win_rate">Win Rate</option>
                        <option value="average_time">Average Time</option>
                    </select>
                )}
            </div>

            {/* Content */}
            {authLoading ? (
                <div className="text-center text-text-secondary py-10 animate-pulse">
                    Checking authentication...
                </div>
            ) : scope === "friends" && !loggedIn ? (
                <div className="text-center bg-bg-secondary border border-border-primary rounded-xl p-10 text-text-secondary">
                    <Lock size={28} className="mx-auto mb-3 opacity-60" />
                    <p className="text-lg">You must be logged in to view friends ranking.</p>
                </div>
            ) : (
                <div className="bg-bg-secondary rounded-2xl border border-border-primary overflow-hidden shadow-sm">
                    <div className="grid grid-cols-4 font-semibold text-text-secondary bg-bg-tertiary px-4 py-3">
                        <span>#</span>
                        <span>User</span>
                        <span>{rankingType === "users" ? "Win Rate" : "Time"}</span>
                        <span>Games</span>
                    </div>

                    {loading ? (
                        <div className="p-6 text-center text-text-secondary animate-pulse">
                            Loading statistics...
                        </div>
                    ) : stats.length === 0 ? (
                        <div className="p-6 text-center text-text-secondary">
                            No data available.
                        </div>
                    ) : (
                        stats.map((row, idx) => (
                            <div
                                key={row.user_id || idx}
                                className="grid grid-cols-4 px-4 py-3 border-t border-border-primary hover:bg-bg-tertiary/50 transition"
                            >
                <span className="font-medium text-text-primary">
                  {(page - 1) * 10 + idx + 1}
                </span>
                                <span className="text-text-primary">{row.username || "Anonymous"}</span>
                                <span className="text-accent-primary">
                  {rankingType === "users"
                      ? `${(row.win_rate * 100).toFixed(1)}%`
                      : `${row.time}s`}
                </span>
                                <span className="text-text-secondary">
                  {row.games_played || row.total_games}
                </span>
                            </div>
                        ))
                    )}
                </div>
            )}

            {/* Pagination */}
            {!(scope === "friends" && !loggedIn) && (
                <div className="flex justify-center items-center gap-4 mt-6">
                    <button
                        disabled={page === 1}
                        onClick={() => setPage((p) => p - 1)}
                        className="p-2 rounded-lg bg-bg-secondary border border-border-primary text-text-secondary disabled:opacity-40 hover:text-accent-primary"
                    >
                        <ChevronLeft size={20} />
                    </button>
                    <span className="text-text-secondary">
            Page <span className="text-text-primary">{page}</span> / {totalPages}
          </span>
                    <button
                        disabled={page >= totalPages}
                        onClick={() => setPage((p) => p + 1)}
                        className="p-2 rounded-lg bg-bg-secondary border border-border-primary text-text-secondary disabled:opacity-40 hover:text-accent-primary"
                    >
                        <ChevronRight size={20} />
                    </button>
                </div>
            )}
        </div>
    );
}
