import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

console.info("main.tsx: Attempting to render React application into the DOM.");
createRoot(document.getElementById("root")!).render(<App />);
console.info("main.tsx: Application rendered successfully.");