import React, {useEffect, useState} from "react";
import { useFriends } from "../contexts/FriendsContext";
import FriendCard from "../components/FriendCard";
import {useGame} from "../contexts/GameServiceContext";

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
        searchPage,
        searchTotalPages,
        setSearchPage,
    } = useFriends();

    const {sendLobbyInvitation} = useGame();
    const [activeTab, setActiveTab] = useState("friends");
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState([]);

    // SEARCH
    const handleSearch = async (e) => {
        e.preventDefault();
        if (!searchQuery.trim()) return;

        const results = await searchUsers(searchQuery, searchPage);
        setSearchResults(results);
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

            <span className="text-text-secondary text-sm">Page {page} / {totalPages}</span>

            <button
                className="px-3 py-1 text-sm rounded bg-bg-secondary border border-border-primary disabled:opacity-50"
                onClick={onNext}
                disabled={page >= totalPages || loading}
            >
                Next
            </button>
        </div>
    );

    const renderTab = () => {
        if (loading)
            return <div className="text-text-secondary text-center py-6">Loading...</div>;

        switch (activeTab) {
            // ---------------------------------------------------------
            // FRIENDS
            // ---------------------------------------------------------
            case "friends":
                return (
                    <>
                        {friends.length === 0 ? (
                            <div className="text-text-secondary text-center py-6">
                                You have no friends yet 😢
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {friends.map(friend => (
                                <FriendCard
                                    key={friend.id}
                                    avatar={friend.avatar_url ?? "/avatar.svg"}
                                    nickname={friend.nickname}
                                    variant="friend"
                                    onInvite={() => console.log("Invite not implemented yet")}
                                    onRemove={() => removeFriend(friend.id)}
                                    onChallenge={() => sendLobbyInvitation(friend.id)}
                                />
                            ))}
                            </div>
                        )}

                        {renderPagination(
                            friendsPage,
                            friendsTotalPages,
                            () => loadFriends(friendsPage - 1),
                            () => loadFriends(friendsPage + 1)
                        )}
                    </>
                );

            // ---------------------------------------------------------
            // REQUESTS
            // ---------------------------------------------------------
            case "requests":
                return (
                    <>
                        <h3 className="text-lg font-semibold text-text-primary mb-2">Incoming</h3>
                        {friendRequests.length === 0 ? (
                            <div className="text-text-secondary mb-4">No incoming requests</div>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {friendRequests.map(r => (
                                    <FriendCard
                                        key={r.id}
                                        avatar={r.user.avatar_url}
                                        nickname={r.user.nickname}
                                        type="incoming"
                                        onAccept={() => acceptFriendRequest(r.id)}
                                        onReject={() => rejectFriendRequest(r.id)}
                                    />
                                ))}
                            </div>
                        )}

                        <h3 className="text-lg font-semibold text-text-primary mb-2">Sent</h3>
                        {sentRequests.length === 0 ? (
                            <div className="text-text-secondary">No sent requests</div>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {sentRequests.map(r => (
                                    <FriendCard
                                        key={r.id}
                                        avatar={r.friend.avatar_url}
                                        nickname={r.friend.nickname}
                                        type="sent"
                                        onCancel={() => rejectFriendRequest(r.id)} // or cancel endpoint
                                     />

                        ))}
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

            // ---------------------------------------------------------
            // ADD FRIEND
            // ---------------------------------------------------------
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

                        {searchResults.length === 0 ? (
                            <div className="text-text-secondary text-center py-6">
                                Search for new friends 🔍
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {searchResults.map(u => (
                                    <FriendCard
                                        key={u.id}
                                        avatar={u.avatar_url}
                                        nickname={u.nickname}
                                        type="search"
                                        onAdd={() => sendFriendRequest(u.id)}
                                        onChallenge={() => sendLobbyInvitation(u.id)}
                                    />

                                ))}
                            </div>
                        )}

                        {searchResults.length > 0 &&
                            renderPagination(
                                searchPage,
                                searchTotalPages,
                                async () => {
                                    const newPage = searchPage - 1;
                                    setSearchPage(newPage);
                                    setSearchResults(await searchUsers(searchQuery, newPage));
                                },
                                async () => {
                                    const newPage = searchPage + 1;
                                    setSearchPage(newPage);
                                    setSearchResults(await searchUsers(searchQuery, newPage));
                                }
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
                    {["friends", "requests", "add"].map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`pb-2 ${
                                activeTab === tab
                                    ? "text-accent-primary border-b-2 border-accent-primary"
                                    : "text-text-secondary"
                            }`}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </button>
                    ))}
                </div>

                <div>{renderTab()}</div>
            </main>
        </div>
    );
}
