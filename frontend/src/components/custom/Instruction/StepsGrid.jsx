import React from 'react';
import StepCard from '@/components/custom/Instruction/StepCard';
import { FileArchive, ListChecks, BarChart3, Filter } from 'lucide-react';

const StepsGrid = () => {
  const steps = [
    {
      number: 1,
      title: 'Upload',
      description: 'Drag and drop your project ZIP files',
      icon: FileArchive,
    },
    {
      number: 2,
      title: 'Confirm',
      description: 'Review and manage uploaded files',
      icon: ListChecks,
    },
    {
      number: 3,
      title: 'Analyze',
      description: 'Submit to analyze your projects',
      icon: BarChart3,
    },
    {
      number: 4,
      title: 'Review',
      description: 'View and sort project summary',
      icon: Filter,
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-12">
      {steps.map((step) => (
        <StepCard 
          key={step.number}
          number={step.number}
          title={step.title}
          description={step.description}
          icon={step.icon}
        />
      ))}
    </div>
  );
};

export default StepsGrid;
