import Generator from '@/pages/Generator';
import MainPage from "@/pages/Home/Home.jsx";
import Main from '@/pages/Instruction';
import LoginPage from "@/pages/auth/login.jsx";
import SignupPage from "@/pages/auth/signup.jsx";
import { Route, Routes } from 'react-router-dom';
import ProfilesPage from "./pages/ProfilesPage";

import "./App.css";

function App() {
    return (
        <main>
            <Routes>
                <Route path="/" element={<Main />} />
                <Route path="/generate" element={<Generator />} />
                <Route path="/home" element={<MainPage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/signup" element={<SignupPage />} />
                <Route path="/profiles" element={<ProfilesPage />} />
            </Routes>
        </main>
    );
}

export default App;