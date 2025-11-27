import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppLayout from "./pages/AppLayout";
import FriendsPage from "./pages/FriendsPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import NotFoundPage from "./pages/NotFoundPage";
import SettingsPage from "./pages/SettingsPage";
import StatsPage from "./pages/StatsPage";
import GamePageSingle from "./pages/GamePageSingle";
import MultiplayerLobby from "./pages/MultiplayerLobby";
import ProtectedRoute from "./utils/ProtectedRoute";
import MultiGamePage from "./pages/MultiGamePage";


function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<AppLayout />}>
                    <Route index element={<GamePageSingle />} />
                    <Route path="/lobby" element={
                        <ProtectedRoute>
                            <MultiplayerLobby />
                        </ProtectedRoute>
                    } />
                    <Route path="/game" element={
                        <ProtectedRoute>
                            <MultiGamePage />
                        </ProtectedRoute>
                    } />

                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />

                    <Route path="/friends" element={
                        <ProtectedRoute>
                            <FriendsPage />
                        </ProtectedRoute>
                    } />

                    <Route path="/stats" element={<StatsPage />} />

                    <Route path="/settings" element={
                        <ProtectedRoute>
                            <SettingsPage />
                        </ProtectedRoute>
                    } />

                    <Route path="*" element={<NotFoundPage />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;