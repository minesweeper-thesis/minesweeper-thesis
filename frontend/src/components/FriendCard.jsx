import { useState, useRef, useEffect } from "react";
import { EllipsisVerticalIcon } from "@heroicons/react/24/solid";

export default function FriendCard({
                                       avatar,
                                       nickname,
                                       type,           // "friend" | "incoming" | "sent" | "search"
                                       onChallenge,
                                          onAccept,
                                       onReject,
                                       onCancel,
                                       onRemove,
                                       onAdd,
                                   }) {
    const [menuOpen, setMenuOpen] = useState(false);
    const menuRef = useRef(null);

    // close menu when clicked outside
    useEffect(() => {
        const handler = (e) => {
            if (menuRef.current && !menuRef.current.contains(e.target)) {
                setMenuOpen(false);
            }
        };
        document.addEventListener("mousedown", handler);
        return () => document.removeEventListener("mousedown", handler);
    }, []);

    return (
        <div className="p-4 bg-bg-secondary border border-border-primary rounded-xl flex items-center gap-4 relative">

            {/* Avatar */}
            <img
                src={avatar || "/avatar.svg"}
                alt="avatar"
                className="w-12 h-12 rounded-full bg-white border-2 border-border-primary object-cover"
            />

            {/* Username + Action Buttons */}
            <div className="flex flex-col flex-grow">
                <span className="text-text-primary font-semibold">
                    {nickname}
                </span>

                {/* Inline actions depending on type */}
                <div className="flex gap-2 mt-1">

                    {/* Challenge is always inline */}
                    {onChallenge && (
                        <button
                            onClick={onChallenge}
                            className="text-accent-primary text-sm hover:underline"
                        >
                            Challenge
                        </button>
                    )}

                    {/* Incoming request → Accept / Reject */}
                    {type === "incoming" && (
                        <>
                            <button
                                onClick={onAccept}
                                className="px-2 py-1 bg-green-600/20 text-green-500 text-sm rounded-md hover:bg-green-600/30"
                            >
                                Accept
                            </button>

                            <button
                                onClick={onReject}
                                className="px-2 py-1 bg-red-600/20 text-red-500 text-sm rounded-md hover:bg-red-600/30"
                            >
                                Reject
                            </button>
                        </>
                    )}

                    {/* Search result → Add Friend */}
                    {type === "search" && (
                        <button
                            onClick={onAdd}
                            className="text-accent-primary text-sm hover:underline"
                        >
                            Add Friend
                        </button>
                    )}
                </div>
            </div>

            {/* Menu button only for friend / sent */}
            {(type === "friend" || type === "sent") && (
                <div className="relative" ref={menuRef}>
                    <button
                        onClick={() => setMenuOpen(!menuOpen)}
                        className="p-2 rounded-lg hover:bg-bg-tertiary transition"
                    >
                        <EllipsisVerticalIcon className="w-6 h-6 text-text-primary" />
                    </button>

                    {menuOpen && (
                        <div className="absolute right-0 top-10 w-40 bg-bg-secondary border border-border-primary rounded-xl shadow-lg p-2 flex flex-col gap-1 z-20">

                            {type === "friend" && (
                                <button
                                    onClick={() => {
                                        setMenuOpen(false);
                                        onRemove();
                                    }}
                                    className="text-left px-3 py-2 text-text-primary hover:bg-bg-tertiary rounded-lg"
                                >
                                    Remove Friend
                                </button>
                            )}

                            {type === "sent" && (
                                <button
                                    onClick={() => {
                                        setMenuOpen(false);
                                        onCancel();
                                    }}
                                    className="text-left px-3 py-2 text-text-primary hover:bg-bg-tertiary rounded-lg"
                                >
                                    Cancel Request
                                </button>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
