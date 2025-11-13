import React, { useState, useEffect } from "react";
import { useFriends } from "../contexts/FriendsContext";

export default function FriendsPage() {
    const {
        friends,
        friendRequests,
        sentRequests,
        searchUsers,
        sendFriendRequest,
        acceptFriendRequest,
        rejectFriendRequest,
        removeFriend,
        loadFriends,
        loadRequests,
        friendsPage,
        friendsTotalPages,
        requestsPage,
        requestsTotalPages,
        loading,
    } = useFriends();

    const [activeTab, setActiveTab] = useState("friends");
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState([]);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!searchQuery.trim()) {
            setSearchResults([]);
            return;
        }

        try {
            const results = await searchUsers(searchQuery);

            // Placeholder
            if (!Array.isArray(results)) {
                setSearchResults([
                    { id: "1", username: "mock_user_1" },
                    { id: "2", username: "mock_user_2" },
                ]);
            } else {
                setSearchResults(results);
            }
        } catch (err) {
            console.error("Search failed", err);
        }
    };

    const renderPagination = (page, totalPages, onPrev, onNext) => (
        <div className="flex justify-center mt-4 gap-2">
            <button
                className="px-3 py-1 text-sm rounded bg-bg-secondary border border-border-primary disabled:opacity-50"
                onClick={onPrev}
                disabled={page <= 1 || loading}
            >
                Prev
            </button>
            <span className="text-text-secondary text-sm">
        Page {page} of {totalPages}
      </span>
            <button
                className="px-3 py-1 text-sm rounded bg-bg-secondary border border-border-primary disabled:opacity-50"
                onClick={onNext}
                disabled={page >= totalPages || loading}
            >
                Next
            </button>
        </div>
    );

    const renderFriendCard = (friend) => (
        <div
            key={friend.id}
            className="flex items-center justify-between p-3 bg-bg-secondary border border-border-primary rounded-xl"
        >
            <div className="text-text-primary font-medium">{friend.username}</div>
            <button
                onClick={() => removeFriend(friend.id)}
                className="text-accent-primary hover:underline"
            >
                Remove
            </button>
        </div>
    );

    const renderRequestCard = (req, type = "incoming") => (
        <div
            key={req.id}
            className="flex items-center justify-between p-3 bg-bg-secondary border border-border-primary rounded-xl"
        >
            <div className="text-text-primary font-medium">{req.from_user?.username || req.to_user?.username}</div>
            {type === "incoming" ? (
                <div className="flex gap-2">
                    <button
                        onClick={() => acceptFriendRequest(req.id)}
                        className="px-2 py-1 text-sm bg-green-600/20 text-green-500 rounded-md hover:bg-green-600/30"
                    >
                        Accept
                    </button>
                    <button
                        onClick={() => rejectFriendRequest(req.id)}
                        className="px-2 py-1 text-sm bg-red-600/20 text-red-500 rounded-md hover:bg-red-600/30"
                    >
                        Reject
                    </button>
                </div>
            ) : (
                <span className="text-text-secondary text-sm">Pending</span>
            )}
        </div>
    );

    const renderTab = () => {
        if (loading) {
            return <div className="text-text-secondary text-center py-6">Loading...</div>;
        }

        switch (activeTab) {
            case "friends":
                return (
                    <>
                        {friends.length === 0 ? (
                            <div className="text-text-secondary text-center py-6">You have no friends yet 😢</div>
                        ) : (
                            <div className="flex flex-col gap-2">{friends.map(renderFriendCard)}</div>
                        )}
                        {renderPagination(
                            friendsPage,
                            friendsTotalPages,
                            () => loadFriends(friendsPage - 1),
                            () => loadFriends(friendsPage + 1)
                        )}
                    </>
                );

            case "requests":
                return (
                    <>
                        <h3 className="text-lg font-semibold text-text-primary mb-2">Incoming Requests</h3>
                        {friendRequests.length === 0 ? (
                            <div className="text-text-secondary mb-4">No incoming friend requests.</div>
                        ) : (
                            <div className="flex flex-col gap-2 mb-4">
                                {friendRequests.map((req) => renderRequestCard(req, "incoming"))}
                            </div>
                        )}
                        <h3 className="text-lg font-semibold text-text-primary mb-2">Sent Requests</h3>
                        {sentRequests.length === 0 ? (
                            <div className="text-text-secondary mb-4">No sent friend requests.</div>
                        ) : (
                            <div className="flex flex-col gap-2">
                                {sentRequests.map((req) => renderRequestCard(req, "sent"))}
                            </div>
                        )}
                        {renderPagination(
                            requestsPage,
                            requestsTotalPages,
                            () => loadRequests(requestsPage - 1),
                            () => loadRequests(requestsPage + 1)
                        )}
                    </>
                );

            case "add":
                return (
                    <div className="flex flex-col gap-3">
                        <form onSubmit={handleSearch} className="flex gap-2">
                            <input
                                type="text"
                                placeholder="Search users..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="flex-grow bg-bg-secondary border border-border-primary rounded-lg px-3 py-2 text-text-primary placeholder-text-secondary"
                            />
                            <button
                                type="submit"
                                className="px-4 py-2 rounded-lg bg-accent-primary text-white hover:opacity-90"
                            >
                                Search
                            </button>
                        </form>

                        {searchResults.length > 0 ? (
                            <div className="flex flex-col gap-2">
                                {searchResults.map((user) => (
                                    <div
                                        key={user.id}
                                        className="flex items-center justify-between p-3 bg-bg-secondary border border-border-primary rounded-xl"
                                    >
                                        <div className="text-text-primary font-medium">{user.username}</div>
                                        <button
                                            onClick={() => sendFriendRequest(user.id)}
                                            className="text-accent-primary hover:underline"
                                        >
                                            Add Friend
                                        </button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-text-secondary text-center py-6">Search for new friends 🔍</div>
                        )}
                    </div>
                );

            default:
                return null;
        }
    };

    return (
        <div className="game flex h-screen justify-center bg-[linear-gradient(135deg,var(--bg-secondary)_0%,var(--bg-tertiary)_100%)] bg-fixed">
            <main className="p-6 flex flex-col gap-6 text-text-primary relative w-full max-w-4xl">
                <div className="flex justify-around border-b border-border-primary pb-2">
                    <button
                        onClick={() => setActiveTab("friends")}
                        className={`pb-2 ${
                            activeTab === "friends"
                                ? "text-accent-primary border-b-2 border-accent-primary"
                                : "text-text-secondary"
                        }`}
                    >
                        Friends
                    </button>
                    <button
                        onClick={() => setActiveTab("requests")}
                        className={`pb-2 ${
                            activeTab === "requests"
                                ? "text-accent-primary border-b-2 border-accent-primary"
                                : "text-text-secondary"
                        }`}
                    >
                        Requests
                    </button>
                    <button
                        onClick={() => setActiveTab("add")}
                        className={`pb-2 ${
                            activeTab === "add"
                                ? "text-accent-primary border-b-2 border-accent-primary"
                                : "text-text-secondary"
                        }`}
                    >
                        Add Friend
                    </button>
                </div>

                <div>{renderTab()}</div>
            </main>
        </div>
    );
}
