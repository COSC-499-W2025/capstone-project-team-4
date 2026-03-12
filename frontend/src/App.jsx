import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Main from "@/pages/Instruction";
import Generator from "@/pages/Generator";
import AccountPage from "@/pages/Account";
import ResumeBuilder from "@/pages/ResumeBuilder";
import LoginPage from "@/pages/auth/login";
import SignupPage from "@/pages/auth/signup";
import { isAuthenticated } from "@/lib/auth";
import "./App.css";

function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function App() {
  return (
    <main>
      <Routes>
        <Route path="/" element={<Main />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route
          path="/generate"
          element={
            <ProtectedRoute>
              <Generator />
            </ProtectedRoute>
          }
        />
        <Route
          path="/account"
          element={
            <ProtectedRoute>
              <AccountPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/resume-builder"
          element={
            <ProtectedRoute>
              <ResumeBuilder />
            </ProtectedRoute>
          }
        />
      </Routes>
    </main>
  );
}

export default App;
