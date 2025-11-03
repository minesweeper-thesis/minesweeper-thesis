import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import './components/ThemeProvider.js';
import App from "./App";
import {AuthProvider} from "./contexts/AuthContext";

ReactDOM.createRoot(document.getElementById('root')).render(

    <AuthProvider>
        <App />
    </AuthProvider>
);