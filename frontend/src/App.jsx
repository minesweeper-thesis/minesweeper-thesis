import { BrowserRouter, Routes, Route } from 'react-router-dom';
import GamePage from "./pages/GamePage";
import AppLayout from "./pages/AppLayout";
import FriendsPage from "./pages/FriendsPage";

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<AppLayout />}>
                    <Route index element={<GamePage />} />
                    <Route path="/friends" element={<FriendsPage />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;