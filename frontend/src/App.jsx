/*import MainPage from "@/pages/Home/Home.jsx";
import LoginPage from "@/pages/auth/login.jsx";
import SignupPage from "@/pages/auth/signup.jsx";
import { Route, Routes } from "react-router-dom";
import "./App.css";
*/

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Main from '@/pages/Instruction';
import Generator from '@/pages/Generator';
import "./App.css";

function App() {
    return (
        <main>
        <Routes>
            <Route path="/" element={<Main />} />
            <Route path="/generate" element={<Generator />} />
        </Routes>
        </main>
    );
}

export default App;
