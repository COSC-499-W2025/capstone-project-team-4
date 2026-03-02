import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

const DataPrivacyConsent = ({ isOpen, onClose, onAccept }) => {
  const [isChecked, setIsChecked] = useState(false);

  const handleAccept = () => {
    if (isChecked) {
      onAccept();
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Data Privacy Consent</DialogTitle>
          <DialogDescription>
            Please review and accept our data privacy policy
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          <div className="space-y-4 text-sm text-gray-700">
            <p>
              By uploading your project files, you consent to:
            </p>
            <ul className="list-disc pl-5 space-y-2">
              <li>Analysis of your project structure and contributions</li>
              <li>Temporary storage of your files for processing</li>
              <li>Generation of a resume based on your project data</li>
            </ul>
            <p className="font-medium">
              We do not share your data with third parties and will delete it after processing.
            </p>
          </div>

          <div className="flex items-start space-x-2 mt-6">
            <Checkbox
              id="consent"
              checked={isChecked}
              onCheckedChange={setIsChecked}
            />
            <label
              htmlFor="consent"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              I have read and agree to the data privacy policy
            </label>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleAccept} disabled={!isChecked}>
            Accept & Continue
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default DataPrivacyConsent;
