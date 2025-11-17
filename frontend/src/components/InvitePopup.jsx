import React, { useState } from "react";
import { useFriends } from "../contexts/FriendsContext";
import { useGame } from "../contexts/GameServiceContext";

export default function InvitePopup({ onClose }) {
    const {
        searchUsers,
        searchPage,
        searchTotalPages,
        setSearchPage,
    } = useFriends();

    const { sendLobbyInvitation } = useGame();

    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        const users = await searchUsers(query, searchPage);
        setResults(users);
        setLoading(false);
    };

    const loadPrev = async () => {
        const newPage = searchPage - 1;
        setSearchPage(newPage);
        setResults(await searchUsers(query, newPage));
    };

    const loadNext = async () => {
        const newPage = searchPage + 1;
        setSearchPage(newPage);
        setResults(await searchUsers(query, newPage));
    };

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex justify-center items-center z-50">
            <div className="bg-bg-secondary border border-border-primary rounded-xl shadow-xl w-full max-w-lg p-6 relative">

                {/* Close */}
                <button
                    className="absolute top-3 right-3 text-text-secondary hover:text-text-primary"
                    onClick={onClose}
                >
                    ✕
                </button>

                <h2 className="text-xl font-semibold text-text-primary mb-4">Invite players</h2>

                {/* SEARCH BAR */}
                <form onSubmit={handleSearch} className="flex gap-2 mb-4">
                    <input
                        type="text"
                        placeholder="Search users..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="flex-grow bg-bg-tertiary border border-border-primary rounded-lg px-3 py-2 text-text-primary placeholder-text-secondary"
                    />
                    <button
                        type="submit"
                        className="px-4 py-2 rounded-lg bg-accent-primary text-white hover:bg-accent-secondary transition"
                    >
                        Search
                    </button>
                </form>

                {/* RESULTS */}
                {loading ? (
                    <div className="text-center text-text-secondary py-4">Searching...</div>
                ) : results.length === 0 ? (
                    <div className="text-center text-text-secondary py-6">
                        Search for players to invite 🔍
                    </div>
                ) : (
                    <div className="flex flex-col gap-3 max-h-80 overflow-y-auto">
                        {results.map((u) => (
                            <div
                                key={u.id}
                                className="flex justify-between items-center p-3 bg-bg-tertiary border border-border-primary rounded-lg"
                            >
                                <div className="flex items-center gap-3">
                                    <img
                                        src={u.avatar_url ?? "/avatar.svg"}
                                        className="w-10 h-10 rounded-lg"
                                    />
                                    <span className="font-medium">{u.nickname}</span>
                                </div>

                                <button
                                    className="px-3 py-1 text-sm rounded bg-accent-primary text-white hover:bg-accent-secondary"
                                    onClick={() => sendLobbyInvitation(u.id)}
                                >
                                    Invite
                                </button>
                            </div>
                        ))}
                    </div>
                )}

                {/* PAGINATION */}
                {results.length > 0 && (
                    <div className="flex justify-center mt-4 gap-3">
                        <button
                            className="px-3 py-1 rounded bg-bg-tertiary border border-border-primary disabled:opacity-50"
                            disabled={searchPage <= 1}
                            onClick={loadPrev}
                        >
                            Prev
                        </button>

                        <span className="text-text-secondary text-sm">
                            Page {searchPage} / {searchTotalPages}
                        </span>

                        <button
                            className="px-3 py-1 rounded bg-bg-tertiary border border-border-primary disabled:opacity-50"
                            disabled={searchPage >= searchTotalPages}
                            onClick={loadNext}
                        >
                            Next
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
