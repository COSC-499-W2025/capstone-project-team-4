import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const StepCard = ({ number, title, description, icon: Icon }) => {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex flex-col items-center text-center space-y-3">
          {/* Number Badge */}
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-blue-600 font-bold text-2xl">
              {number}
            </span>
          </div>
          
          {/* Icon */}
          <Icon className="h-8 w-8 text-blue-600" />
          
          {/* Title */}
          <CardTitle className="text-xl">
            {title}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-gray-600 text-center text-sm">
          {description}
        </p>
      </CardContent>
    </Card>
  );
};

export default StepCard;
