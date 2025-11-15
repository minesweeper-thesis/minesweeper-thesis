import React, { createContext, useContext, useState, useEffect, useCallback } from "react";

const FriendsContext = createContext(null);

export const FriendsProvider = ({ children }) => {
    const [friends, setFriends] = useState([]);
    const [friendRequests, setFriendRequests] = useState([]);
    const [sentRequests, setSentRequests] = useState([]);

    const [friendsPage, setFriendsPage] = useState(1);
    const [friendsTotalPages, setFriendsTotalPages] = useState(1);

    const [requestsPage, setRequestsPage] = useState(1);
    const [requestsTotalPages, setRequestsTotalPages] = useState(1);

    const [loading, setLoading] = useState(false);

    const [searchPage, setSearchPage] = useState(1);
    const [searchTotalPages, setSearchTotalPages] = useState(1);

    const authFetch = async (url, options = {}) => {
        const res = await fetch(url, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {}),
            },
            credentials: 'include',
        });
        if (!res.ok) {
            const text = await res.text();
            throw new Error(text || res.statusText);
        }
        return res.json();
    };

    const loadFriends = useCallback(
        async (page = 1) => {
            setLoading(true);
            try {
                const data = await authFetch(`api/friends?page=${page}`);
                setFriends(data.items || []);
                setFriendsPage(data.page || page);
                setFriendsTotalPages(data.pages || 1);
            } catch (e) {
                console.error("Failed to load friends", e);
            } finally {
                setLoading(false);
            }
        },
        []
    );

    const loadRequests = useCallback(
        async (page = 1) => {
            setLoading(true);
            try {
                const [pending, sent] = await Promise.all([
                    authFetch(`api/friend-requests/pending?page=${page}`),
                    authFetch(`api/friend-requests/sent?page=${page}`),
                ]);
                setFriendRequests(pending.items || []);
                setSentRequests(sent.items || []);
                setRequestsPage(pending.page || page);
                setRequestsTotalPages(pending.pages || 1);
            } catch (e) {
                console.error("Failed to load requests", e);
            } finally {
                setLoading(false);
            }
        },
        []
    );

    const reload = useCallback(() => {
        loadFriends(friendsPage);
        loadRequests(requestsPage);
    }, [friendsPage, requestsPage]);

    useEffect(() => {
        reload();
    }, []);

    const sendFriendRequest = async (friendId) => {
        await authFetch(`api/friend-requests?friend_id=${friendId}`, { method: "POST" });
        reload();
    };

    const acceptFriendRequest = async (requestId) => {
        await authFetch(`api/friend-requests/${requestId}/accept`, { method: "PUT" });
        reload();
    };

    const rejectFriendRequest = async (requestId) => {
        await authFetch(`api/friend-requests/${requestId}/reject`, { method: "PUT" });
        reload();
    };

    const removeFriend = async (friendId) => {
        await authFetch(`api/friends/${friendId}`, { method: "DELETE" });
        reload();
    };

    const searchUsers = async (query, page = 1) => {
        try {
            const data = await authFetch(
                `api/search?query=${encodeURIComponent(query)}&page=${page}&size=10`
            );

            setSearchPage(data.page || 1);
            setSearchTotalPages(data.pages || 1);

            return data.items || [];
        } catch (e) {
            console.error("Search failed", e);
            return [];
        }
    };


    return (
        <FriendsContext.Provider
            value={{
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
            }}
        >
            {children}
        </FriendsContext.Provider>
    );
};

export const useFriends = () => useContext(FriendsContext);
