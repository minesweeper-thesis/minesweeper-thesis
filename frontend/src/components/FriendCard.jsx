import { useState, useRef, useEffect } from "react";
import { EllipsisVerticalIcon } from "@heroicons/react/24/solid";


export default function FriendCard({
                                       avatar = "/avatar.svg",
                                       nickname = "Unknown",
                                       type = "friend",
                                       onChallenge = () => {},
                                       onAccept = () => {},
                                       onReject = () => {},
                                       onCancel = () => {},
                                       onRemove = () => {},
                                       onAdd = () => {},
                                   }) {
    const [open, setOpen] = useState(false);
    const menuRef = useRef(null);
    const btnRef = useRef(null);

    // close menu on outside click or Escape
    useEffect(() => {
        function handleClick(e) {
            if (menuRef.current && !menuRef.current.contains(e.target) && btnRef.current && !btnRef.current.contains(e.target)) {
                setOpen(false);
            }
        }
        function handleKey(e) {
            if (e.key === "Escape") setOpen(false);
        }
        document.addEventListener("mousedown", handleClick);
        document.addEventListener("touchstart", handleClick);
        document.addEventListener("keydown", handleKey);
        return () => {
            document.removeEventListener("mousedown", handleClick);
            document.removeEventListener("touchstart", handleClick);
            document.removeEventListener("keydown", handleKey);
        };
    }, []);

    return (
        <div className="p-3 bg-bg-secondary border border-border-primary rounded-xl flex items-center gap-3 min-w-[240px]">
            {/* Avatar */}
            <div className="flex-shrink-0">
                <img
                    src={avatar || "/avatar.svg"}
                    alt={`${nickname} avatar`}
                    className="w-12 h-12 rounded-full bg-white p-1 border-2 border-border-primary object-cover"
                />
            </div>

            <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                    <span className="text-text-primary font-semibold truncate">{nickname}</span>
                </div>

                <div className="mt-2 flex items-center gap-2">
                    {type === "incoming" && (
                        <>
                            <button
                                onClick={onAccept}
                                className="px-2 py-1 text-sm bg-green-600/20 text-green-500 rounded-md hover:bg-green-600/30"
                            >
                                Accept
                            </button>
                            <button
                                onClick={onReject}
                                className="px-2 py-1 text-sm bg-red-600/20 text-red-500 rounded-md hover:bg-red-600/30"
                            >
                                Reject
                            </button>
                        </>
                    )}

                    {type === "search" && (
                        <button
                            onClick={onAdd}
                            className="px-2 py-1 text-sm text-accent-primary rounded-md hover:underline"
                        >
                            Add Friend
                        </button>
                    )}
                </div>
            </div>

            <div className="flex items-center gap-1 ml-1">
                {onChallenge && (
                    <button
                        onClick={onChallenge}
                        className="flex-shrink-0 px-3 py-1.5 text-sm rounded-md bg-accent-primary text-bg-primary font-medium hover:opacity-90"
                        aria-label={`Challenge ${nickname}`}
                    >
                        Invite
                    </button>
                )}

                {/* Menu trigger */}
                {(type === "friend" || type === "sent") && (
                    <div className="relative">
                        <button
                            ref={btnRef}
                            onClick={() => setOpen(o => !o)}
                            className="p-2 rounded-md hover:bg-bg-tertiary focus:outline-none focus:ring-2 focus:ring-accent-primary flex-shrink-0"
                            aria-haspopup="true"
                            aria-expanded={open}
                            aria-label="Open actions"
                        >
                            <EllipsisVerticalIcon className="w-5 h-5 text-text-primary" />
                        </button>

                        {/* Menu */}
                        {open && (
                            <div
                                ref={menuRef}
                                role="menu"
                                aria-label="Friend actions"
                                className="absolute right-0 top-10 z-50 w-44 bg-bg-secondary border border-border-primary rounded-xl shadow-lg p-2"
                            >
                                <div className="flex flex-col">
                                    {type === "friend" && (
                                        <>
                                            <button
                                                onClick={() => { setOpen(false); onRemove(); }}
                                                className="text-left px-3 py-2 text-text-primary hover:bg-bg-tertiary rounded-md"
                                                role="menuitem"
                                            >
                                                Remove Friend
                                            </button>
                                        {/*    <button*/}
                                        {/*    onClick={() => { setOpen(false); }}*/}
                                        {/*    className="text-left px-3 py-2 text-text-primary hover:bg-bg-tertiary rounded-md"*/}
                                        {/*    role="menuitem"*/}
                                        {/*>*/}
                                        {/*    View Profile*/}
                                        {/*</button>*/}
                                        </>
                                    )}

                                    {type === "sent" && (
                                        <button
                                            onClick={() => { setOpen(false); onCancel(); }}
                                            className="text-left px-3 py-2 text-text-primary hover:bg-bg-tertiary rounded-md"
                                            role="menuitem"
                                        >
                                            Cancel Request
                                        </button>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
