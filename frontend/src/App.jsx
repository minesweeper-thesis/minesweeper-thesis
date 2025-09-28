import { BrowserRouter, Routes, Route } from 'react-router-dom';
import GamePage from "./pages/GamePage";
import AppLayout from "./pages/AppLayout";

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<AppLayout />}>
                    <Route index element={<GamePage />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;