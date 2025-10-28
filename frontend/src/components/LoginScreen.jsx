import React, { useState } from 'react';
import '../styles/loginScreen.css';


export default function LoginScreen({ onSwitchToRegister }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        //TODO
        console.log("Logowanie:", { email, password });
    };

    return (
        <div className="login-container">
            <form className="login-form" onSubmit={handleSubmit}>
                <h2>Log In</h2>

                <label>
                    Email:
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </label>

                <label>
                    Password:
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </label>

                <button type="submit">Log In</button>

                <p className="switch-text">
                    No account yet?{' '}
                    <span className="switch-link" >
                    {/*<span className="switch-link" onClick={onSwitchToRegister}>*/}
            Register
          </span>
                </p>
            </form>
        </div>
    );
}
