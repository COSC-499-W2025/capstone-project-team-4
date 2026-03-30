import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

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
            <p>By uploading your project files, you consent to:</p>
            <ul className="list-disc pl-5 space-y-2">
              <li>Analysis of your project structure and contributions</li>
              <li>Temporary storage of your files for processing</li>
              <li>Generation of a resume based on your project data</li>
            </ul>
            <p className="font-medium">
              We do not share your data with third parties and will delete it
              after processing.
            </p>
          </div>

          <div className="mt-6 flex items-start space-x-2 rounded-lg border border-gray-300 bg-gray-50 p-3">
            <Checkbox
              id="consent"
              checked={isChecked}
              onCheckedChange={setIsChecked}
              className="mt-0.5 size-5 border-2 border-gray-600 data-[state=checked]:border-gray-800 data-[state=checked]:bg-gray-700 data-[state=checked]:text-white focus-visible:ring-gray-600/60"
            />
            <label
              htmlFor="consent"
              className="text-sm font-semibold leading-none text-gray-800 peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
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
