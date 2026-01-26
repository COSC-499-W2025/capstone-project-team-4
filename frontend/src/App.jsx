import MainPage from "@/pages/Home/Home.jsx";
import LoginPage from "@/pages/auth/login.jsx";
import SignupPage from "@/pages/auth/signup.jsx";
import { Route, Routes } from "react-router-dom";
import "./App.css";
import ProfilesPage from "./pages/ProfilesPage";

function App() {
    return (
        <main>
        <Routes>
            {/* Home */}
            <Route path="/" element={<MainPage />} />
            {/* Auth */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            {/* User Profiles */}
            <Route path="/profiles" element={<ProfilesPage />} />
        </Routes>
        </main>
    );
}

export default App;
