import React from 'react';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';

const InstructionHeader = ({ onGetStarted }) => {
  return (
    <div className="text-center mb-8">
      <h1 className="text-5xl font-bold text-gray-900 mb-4">
        Resume Generator
      </h1>
      <p className="text-lg text-gray-600 mb-6">
        Transform your project files into a professional resume in 4 easy steps
      </p>
      
      {/* Get Started Button */}
      <Button 
        onClick={onGetStarted}
        size="lg"
        className="px-8 py-4 text-lg"
      >
        Get Started
        <ArrowRight className="ml-2 h-5 w-5" />
      </Button>
    </div>
  );
};

export default InstructionHeader;
