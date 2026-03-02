import React from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '@/components/Navigation';
import InstructionHeader from '@/components/custom/Instruction/InstructionHeader';
import StepsGrid from '@/components/custom/Instruction/StepsGrid';

const Main = () => {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate('/generate');
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      
      <div className="flex-1 bg-gradient-to-b from-blue-50 to-white py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <InstructionHeader onGetStarted={handleGetStarted} />
          
          <StepsGrid />
        </div>
      </div>
    </div>
  );
};

export default Main;