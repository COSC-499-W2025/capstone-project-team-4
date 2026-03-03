/*import MainPage from "@/pages/Home/Home.jsx";
import LoginPage from "@/pages/auth/login.jsx";
import SignupPage from "@/pages/auth/signup.jsx";
import { Route, Routes } from "react-router-dom";
import "./App.css";
*/

import Generator from '@/pages/Generator';
import Main from '@/pages/Instruction';
import { Route, Routes } from 'react-router-dom';
import "./App.css";
import ProfilesPage from "./pages/ProfilesPage";

function App() {
    return (
        <main>
        <Routes>
            <Route path="/" element={<Main />} />
            <Route path="/generate" element={<Generator />} />
            <Route path="/profiles" element={<ProfilesPage />} />
        </Routes>
        </main>
    );
}

export default App;
