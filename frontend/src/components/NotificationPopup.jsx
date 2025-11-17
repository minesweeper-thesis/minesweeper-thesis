import { useEffect, useState } from "react";
import { useGame } from "../contexts/GameServiceContext";
import { useFriends } from "../contexts/FriendsContext";
import { v4 as uuidv4 } from "uuid";
import { Bell } from "lucide-react";

export default function NotificationPopup() {
    const { lastMessage, socket, acceptGameInvite, rejectGameInvite } = useGame();
    const { acceptFriendRequest, rejectFriendRequest } = useFriends();

    const [notifications, setNotifications] = useState([]);
    const [isOpen, setIsOpen] = useState(false);

    useEffect(() => {
        if (!lastMessage) return;

        try {
            const msg = lastMessage;

            if (["friend_request", "invitation"].includes(msg.type)) {
                setNotifications(prev => {
                    if (prev.some(n => n.id === msg.id)) return prev;
                    return [
                        ...prev,
                        { ...msg, id: msg.id || uuidv4(), timestamp: Date.now() }
                    ];
                });
            }
        } catch (e) {
            console.warn("Nieprawidłowe powiadomienie:", lastMessage);
        }
    }, [lastMessage]);

    const handleAccept = (id) => {
        const notif = notifications.find(n => n.id === id);
        if (!notif) return;

        if (notif.type === "friend_request") {
            acceptFriendRequest(notif.id);
        } else if (notif.type === "invitation") {
            acceptGameInvite(notif.id, notif.lobby.id);
        }

        setNotifications(prev => prev.filter(n => n.id !== id));
    };

    const handleReject = (id) => {
        const notif = notifications.find(n => n.id === id);
        if (!notif) return;

        if (notif.type === "friend_request") {
            rejectFriendRequest(notif.id);
        } else if (notif.type === "invitation") {
            rejectGameInvite(notif.id);
        }

        setNotifications(prev => prev.filter(n => n.id !== id));
    };

    const unreadCount = notifications.length;

    const getMessage = (msg) => {
        switch(msg.type) {
            case "friend_request": return `${msg.user.nickname} wants to be your friend!`;
            case "invitation": return `${msg.lobby.host.nickname} invites you to play!`;
            default: return "Wrong type";
        }
    };

    return (
        <div className="fixed top-1/2 right-0 z-50 transform -translate-y-1/2 flex">
            <button
                onClick={() => setIsOpen(prev => !prev)}
                className="w-10 h-20 bg-bg-tertiary border border-border-primary rounded-l-xl shadow-lg flex flex-col items-center justify-center gap-2 cursor-pointer relative transition-opacity duration-200 hover:opacity-90"
            >
                <Bell className="text-text-primary"/>
                {unreadCount > 0 && (
                    <span className="absolute top-2 right-2 px-2 py-0.5 text-xs text-white bg-accent-primary rounded-full shadow">
                        {unreadCount}
                    </span>
                )}
            </button>

            <div
                className={`
                    bg-bg-secondary border border-border-primary border-r-0
                    rounded-l-xl shadow-xl
                    overflow-hidden
                    transition-all duration-300
                    ${isOpen ? "w-80 max-w-80" : "w-0 max-w-0"}
                `}
                style={{ maxHeight: "70vh" }}
            >
                {isOpen && (
                    <div className="flex flex-col h-full">
                        <div className="px-4 py-3 bg-bg-tertiary border-b border-border-primary flex justify-between items-center">
                            <span className="font-semibold text-text-primary">Powiadomienia</span>
                        </div>

                        <div className="overflow-y-auto divide-y divide-border-primary">
                            {notifications.map(notif => (
                                <div key={notif.id} className="px-4 py-3 text-text-primary">
                                    <div className="flex items-center gap-2">
                                        <span>{getMessage(notif)}</span>
                                        <span className="flex-1">{notif.message}</span>
                                    </div>

                                    <div className="flex gap-2 mt-2">
                                        <button
                                            onClick={() => handleAccept(notif.id)}
                                            className="px-2 py-1 text-xs bg-accent-primary text-white rounded hover:bg-accent-secondary transition"
                                        >
                                            Accept
                                        </button>

                                        <button
                                            onClick={() => handleReject(notif.id)}
                                            className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-500 transition"
                                        >
                                            Reject
                                        </button>
                                    </div>
                                </div>
                            ))}

                            {notifications.length === 0 && (
                                <div className="px-4 py-3 text-text-primary/70">
                                    No notifications found.
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
