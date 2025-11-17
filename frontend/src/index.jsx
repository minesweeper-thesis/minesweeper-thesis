import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from "./App";
import {AuthProvider} from "./contexts/AuthContext";
import {FriendsProvider} from "./contexts/FriendsContext";
import { initTheme } from './contexts/ThemeProvider.js';
import {GameServiceProvider} from "./contexts/GameServiceContext";

initTheme();
ReactDOM.createRoot(document.getElementById('root')).render(

    <AuthProvider>
        <GameServiceProvider>
            <FriendsProvider>
                <App />
            </FriendsProvider>
        </GameServiceProvider>
    </AuthProvider>
);
