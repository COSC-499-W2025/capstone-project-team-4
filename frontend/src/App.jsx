import MainPage from "@/pages/Home/Home.jsx";
import LoginPage from "@/pages/auth/login.jsx";
import SignupPage from "@/pages/auth/signup.jsx";
import { Route, Routes, Router } from "react-router-dom";
import "./App.css";
import Test from "./pages/Test";

function App() {
  return (
    <main>
      <Routes>
        {/* Home */}
        <Route path="/" element={<MainPage />} />
        {/* Auth */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* Testing */}
        <Route path="/peer-testing" Component={Test}></Route>
      </Routes>
    </main>
  );
}

export default App;
