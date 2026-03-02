import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { X } from 'lucide-react';

const EditProjectModal = ({ isOpen, onClose, project, onSave }) => {
  const [formData, setFormData] = useState({
    name: project?.name || '',
    contributions: project?.contributions || 0,
    date: project?.date ? new Date(project.date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
    projectStartedAt: project?.projectStartedAt ? new Date(project.projectStartedAt).toISOString().split('T')[0] : '',
    description: project?.description || '',
    languages: project?.languages || [],
    frameworks: project?.frameworks || [],
    skills: project?.skills || [],
    toolsAndTechnologies: project?.toolsAndTechnologies || [],
  });

  const [newLanguage, setNewLanguage] = useState('');
  const [newFramework, setNewFramework] = useState('');
  const [newSkill, setNewSkill] = useState('');
  const [newTool, setNewTool] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'contributions' ? parseInt(value) || 0 : value
    }));
  };

  // Language handlers
  const handleAddLanguage = () => {
    if (newLanguage.trim() && !formData.languages.includes(newLanguage.trim())) {
      setFormData(prev => ({
        ...prev,
        languages: [...prev.languages, newLanguage.trim()]
      }));
      setNewLanguage('');
    }
  };

  const handleRemoveLanguage = (index) => {
    setFormData(prev => ({
      ...prev,
      languages: prev.languages.filter((_, i) => i !== index)
    }));
  };

  // Framework handlers
  const handleAddFramework = () => {
    if (newFramework.trim() && !formData.frameworks.includes(newFramework.trim())) {
      setFormData(prev => ({
        ...prev,
        frameworks: [...prev.frameworks, newFramework.trim()]
      }));
      setNewFramework('');
    }
  };

  const handleRemoveFramework = (index) => {
    setFormData(prev => ({
      ...prev,
      frameworks: prev.frameworks.filter((_, i) => i !== index)
    }));
  };

  // Skill handlers
  const handleAddSkill = () => {
    if (newSkill.trim() && !formData.skills.includes(newSkill.trim())) {
      setFormData(prev => ({
        ...prev,
        skills: [...prev.skills, newSkill.trim()]
      }));
      setNewSkill('');
    }
  };

  const handleRemoveSkill = (index) => {
    setFormData(prev => ({
      ...prev,
      skills: prev.skills.filter((_, i) => i !== index)
    }));
  };

  // Tools & Technologies handlers
  const handleAddTool = () => {
    if (newTool.trim() && !formData.toolsAndTechnologies.includes(newTool.trim())) {
      setFormData(prev => ({
        ...prev,
        toolsAndTechnologies: [...prev.toolsAndTechnologies, newTool.trim()]
      }));
      setNewTool('');
    }
  };

  const handleRemoveTool = (index) => {
    setFormData(prev => ({
      ...prev,
      toolsAndTechnologies: prev.toolsAndTechnologies.filter((_, i) => i !== index)
    }));
  };

  const handleSave = () => {
    // Convert dates back to ISO string with time
    const updatedData = {
      ...formData,
      date: new Date(formData.date).toISOString(),
      projectStartedAt: formData.projectStartedAt 
        ? new Date(formData.projectStartedAt).toISOString() 
        : null,
    };
    onSave(updatedData);
    onClose();
  };

  const handleKeyPress = (e, addFunction) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addFunction();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Project Details</DialogTitle>
          <DialogDescription>
            Customize your project information
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Project Name */}
          <div className="space-y-2">
            <Label htmlFor="name">Project Name</Label>
            <Input
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="My Awesome Project"
            />
          </div>

          {/* Files Analyzed */}
          <div className="space-y-2">
            <Label htmlFor="contributions">Files Analyzed</Label>
            <Input
              id="contributions"
              name="contributions"
              type="number"
              value={formData.contributions}
              onChange={handleChange}
              placeholder="0"
            />
          </div>

          {/* Project Start Date */}
          <div className="space-y-2">
            <Label htmlFor="projectStartedAt">Project Start Date</Label>
            <Input
              id="projectStartedAt"
              name="projectStartedAt"
              type="date"
              value={formData.projectStartedAt}
              onChange={handleChange}
            />
            <p className="text-xs text-gray-500">
              When the project was originally started
            </p>
          </div>

          {/* Analyzed Date */}
          <div className="space-y-2">
            <Label htmlFor="date">Analyzed Date</Label>
            <Input
              id="date"
              name="date"
              type="date"
              value={formData.date}
              onChange={handleChange}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Brief description of your project..."
              rows={3}
            />
          </div>

          {/* Languages */}
          <div className="space-y-2">
            <Label>Languages</Label>
            <div className="flex gap-2">
              <Input
                value={newLanguage}
                onChange={(e) => setNewLanguage(e.target.value)}
                onKeyPress={(e) => handleKeyPress(e, handleAddLanguage)}
                placeholder="Add a language (e.g., Python)"
              />
              <Button onClick={handleAddLanguage} type="button">
                Add
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {formData.languages.map((lang, index) => (
                <Badge key={index} variant="secondary" className="text-sm">
                  {lang}
                  <button
                    onClick={() => handleRemoveLanguage(index)}
                    className="ml-2 hover:text-red-600"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>

          {/* Frameworks */}
          <div className="space-y-2">
            <Label>Frameworks</Label>
            <div className="flex gap-2">
              <Input
                value={newFramework}
                onChange={(e) => setNewFramework(e.target.value)}
                onKeyPress={(e) => handleKeyPress(e, handleAddFramework)}
                placeholder="Add a framework (e.g., React)"
              />
              <Button onClick={handleAddFramework} type="button">
                Add
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {formData.frameworks.map((fw, index) => (
                <Badge key={index} variant="outline" className="text-sm">
                  {fw}
                  <button
                    onClick={() => handleRemoveFramework(index)}
                    className="ml-2 hover:text-red-600"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>

          {/* Skills */}
          <div className="space-y-2">
            <Label>Skills</Label>
            <div className="flex gap-2">
              <Input
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                onKeyPress={(e) => handleKeyPress(e, handleAddSkill)}
                placeholder="Add a skill (e.g., API Development)"
              />
              <Button onClick={handleAddSkill} type="button">
                Add
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {formData.skills.map((skill, index) => (
                <Badge key={index} className="text-sm bg-blue-100 text-blue-800">
                  {skill}
                  <button
                    onClick={() => handleRemoveSkill(index)}
                    className="ml-2 hover:text-red-600"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>

          {/* Tools & Technologies */}
          <div className="space-y-2">
            <Label>Tools & Technologies</Label>
            <div className="flex gap-2">
              <Input
                value={newTool}
                onChange={(e) => setNewTool(e.target.value)}
                onKeyPress={(e) => handleKeyPress(e, handleAddTool)}
                placeholder="Add a tool (e.g., Docker, GitHub Actions)"
              />
              <Button onClick={handleAddTool} type="button">
                Add
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {formData.toolsAndTechnologies.map((tool, index) => (
                <Badge key={index} variant="outline" className="text-sm bg-orange-50 text-orange-700 border-orange-200">
                  {tool}
                  <button
                    onClick={() => handleRemoveTool(index)}
                    className="ml-2 hover:text-red-600"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default EditProjectModal;