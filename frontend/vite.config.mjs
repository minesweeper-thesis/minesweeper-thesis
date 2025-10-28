import { defineConfig, loadEnv} from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite'


export default ({ mode }) => {
    process.env = {...process.env, ...loadEnv(mode, process.cwd())};


    return defineConfig({
        plugins: [react(), tailwindcss()],
        server: {
            port: 3000,
            proxy: {
                '/api': {
                    target: process.env.VITE_API_URL,
                    changeOrigin: true,
                    rewrite: (path) => path.replace(/^\/api/, ''),
                },
                '/game_api': {
                    target: process.env.VITE_GAME_URL,
                    changeOrigin: true,
                    rewrite: (path) => path.replace(/^\/game_api\//, ''),
                },
            },
        },
    });
}