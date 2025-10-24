import React, { useState, useEffect, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Clock, Save, Download, AlertCircle, ArrowLeft } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/context/AuthContext";
import { formatDistanceToNow, parseISO } from "date-fns";

const API_BASE_URL = 'https://backend.jkusa.org';

interface Field {
  id: number;
  label: string;
  field_type: string;
  required: boolean;
  position: number;
  default_value?: string;
  options?: string[];
  conditions: Condition[];
}

interface Condition {
  depends_on_field_id: number;
  operator: string;
  value: string;
}

interface Form {
  id: number;
  title: string;
  description: string;
  open_date: string;
  close_date: string;
  status: string;
  target_all_students: boolean;
  target_years: number[];
  fields: Field[];
}

interface Submission {
  id?: number;
  form_id: number;
  student_id: number;
  data: Record<string, any>;
  submitted_at?: string;
  last_edited_at?: string;
  locked: boolean;
}

interface FormStatus {
  form_id: number;
  form_status: string;
  submission_status: string;
  is_locked: boolean;
  time_remaining_seconds: number;
  deadline: string;
  submitted_at?: string;
  last_edited_at?: string;
}

const StudentFormsPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user, makeAuthenticatedRequest } = useAuth();
  const { formId } = useParams<{ formId: string }>();
  const [forms, setForms] = useState<Form[]>([]);
  const [selectedForm, setSelectedForm] = useState<Form | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [formStatus, setFormStatus] = useState<FormStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  // Auto-save functionality
  useEffect(() => {
    if (!formId || !selectedForm || submission?.locked) return;

    const autoSave = setInterval(async () => {
      if (Object.keys(formData).length > 0 && !isSaving) {
        await handleSave();
      }
    }, 30000); // Auto-save every 30 seconds

    return () => clearInterval(autoSave);
  }, [formData, selectedForm, submission, isSaving]);

  // Fetch forms or specific form
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        if (formId) {
          // Fetch specific form and its status/submission
          const [formResponse, statusResponse, submissionResponse] = await Promise.all([
            makeAuthenticatedRequest(`${API_BASE_URL}/registrations/forms/${formId}`),
            makeAuthenticatedRequest(`${API_BASE_URL}/registrations/forms/${formId}/status`),
            makeAuthenticatedRequest(`${API_BASE_URL}/registrations/forms/${formId}/submission`).catch(() => null),
          ]);

          if (formResponse.ok) {
            const form = await formResponse.json();
            setSelectedForm(form);
            setFormData({
              ...form.fields.reduce((acc: any, field: Field) => ({
                ...acc,
                [field.id]: field.default_value || "",
              }), {}),
              ...(submissionResponse && submissionResponse.ok ? (await submissionResponse.json()).data : {}),
            });
          } else {
            throw new Error('Failed to load form');
          }

          if (statusResponse.ok) {
            setFormStatus(await statusResponse.json());
          }

          if (submissionResponse && submissionResponse.ok) {
            setSubmission(await submissionResponse.json());
          }
        } else {
          // Fetch all available forms
          const response = await makeAuthenticatedRequest(`${API_BASE_URL}/registrations/forms?limit=50`);
          if (response.ok) {
            setForms((await response.json()).sort((a: Form, b: Form) => new Date(b.open_date).getTime() - new Date(a.open_date).getTime()));
          } else {
            throw new Error('Failed to load forms');
          }
        }
      } catch (error) {
        toast({ title: "Error", description: (error as Error).message, variant: "destructive" });
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [formId]);

  // Initialize pre-filled fields
  useEffect(() => {
    if (user && selectedForm) {
      setFormData(prev => ({
        ...prev,
        ...(selectedForm.fields.some(f => f.label.toLowerCase().includes("name")) ? {
          [selectedForm.fields.find(f => f.label.toLowerCase().includes("name"))!.id]: `${user.first_name} ${user.last_name}`,
        } : {}),
        ...(selectedForm.fields.some(f => f.label.toLowerCase().includes("email")) ? {
          [selectedForm.fields.find(f => f.label.toLowerCase().includes("email"))!.id]: user.email,
        } : {}),
        ...(selectedForm.fields.some(f => f.label.toLowerCase().includes("registration")) ? {
          [selectedForm.fields.find(f => f.label.toLowerCase().includes("registration"))!.id]: user.registration_number,
        } : {}),
        ...(selectedForm.fields.some(f => f.label.toLowerCase().includes("college")) ? {
          [selectedForm.fields.find(f => f.label.toLowerCase().includes("college"))!.id]: user.college?.name || "",
        } : {}),
        ...(selectedForm.fields.some(f => f.label.toLowerCase().includes("school")) ? {
          [selectedForm.fields.find(f => f.label.toLowerCase().includes("school"))!.id]: user.school?.name || "",
        } : {}),
      }));
    }
  }, [user, selectedForm]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    if (selectedForm) {
      selectedForm.fields.forEach(field => {
        if (field.required && !formData[field.id]) {
          newErrors[field.id] = `${field.label} is required`;
        }
        if (field.field_type === "email" && formData[field.id] && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData[field.id])) {
          newErrors[field.id] = "Invalid email format";
        }
        if (field.field_type === "number" && formData[field.id] && isNaN(Number(formData[field.id]))) {
          newErrors[field.id] = "Must be a number";
        }
      });
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = useCallback(async () => {
    if (!selectedForm || submission?.locked) return;
    setIsSaving(true);
    try {
      const body = { data: formData };
      const url = submission
        ? `${API_BASE_URL}/registrations/forms/${selectedForm.id}/submission`
        : `${API_BASE_URL}/registrations/forms/${selectedForm.id}/submit`;
      const method = submission ? 'PUT' : 'POST';
      const response = await makeAuthenticatedRequest(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (response.ok) {
        const data = await response.json();
        setSubmission(data);
        setLastSaved(new Date());
        toast({ title: "Progress saved" });
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to ${submission ? 'update' : 'submit'} form`);
      }
    } catch (error) {
      toast({ title: "Error", description: (error as Error).message, variant: "destructive" });
    } finally {
      setIsSaving(false);
    }
  }, [selectedForm, formData, submission]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) {
      toast({ title: "Validation Error", description: "Please fix the errors below", variant: "destructive" });
      return;
    }
    await handleSave();
    navigate("/forms");
  };

  const handleDownload = async () => {
    if (!submission) return;
    try {
      const response = await makeAuthenticatedRequest(`${API_BASE_URL}/registrations/forms/${formId}/submissions/export?format=pdf`, { method: 'GET' });
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `submission_${submission.id}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        throw new Error('Failed to download submission');
      }
    } catch (error) {
      toast({ title: "Error", description: (error as Error).message, variant: "destructive" });
    }
  };

  const isFieldVisible = (field: Field) => {
    if (!field.conditions.length) return true;
    return field.conditions.every(condition => {
      const dependsValue = formData[condition.depends_on_field_id];
      if (condition.operator === "equals") {
        return dependsValue === condition.value;
      } else if (condition.operator === "not_equals") {
        return dependsValue !== condition.value;
      }
      return false;
    });
  };

  const renderField = (field: Field) => {
    if (!isFieldVisible(field)) return null;

    const commonProps = {
      id: `field-${field.id}`,
      value: formData[field.id] || "",
      onChange: (e: any) => setFormData({ ...formData, [field.id]: e.target.value }),
      className: `form-input ${errors[field.id] ? 'border-destructive' : ''}`,
      disabled: submission?.locked || field.label.toLowerCase().includes("name") || 
                field.label.toLowerCase().includes("email") || 
                field.label.toLowerCase().includes("registration") || 
                field.label.toLowerCase().includes("college") || 
                field.label.toLowerCase().includes("school"),
      required: field.required,
    };

    switch (field.field_type) {
      case "text":
      case "email":
        return (
          <div key={field.id}>
            <Label htmlFor={`field-${field.id}`}>{field.label} {field.required && '*'}</Label>
            <Input {...commonProps} type={field.field_type} />
            {errors[field.id] && (
              <div className="flex items-center gap-1 text-sm text-destructive mt-1">
                <AlertCircle className="h-4 w-4" />
                {errors[field.id]}
              </div>
            )}
          </div>
        );
      case "textarea":
        return (
          <div key={field.id}>
            <Label htmlFor={`field-${field.id}`}>{field.label} {field.required && '*'}</Label>
            <Textarea {...commonProps} />
            {errors[field.id] && (
              <div className="flex items-center gap-1 text-sm text-destructive mt-1">
                <AlertCircle className="h-4 w-4" />
                {errors[field.id]}
              </div>
            )}
          </div>
        );
      case "number":
        return (
          <div key={field.id}>
            <Label htmlFor={`field-${field.id}`}>{field.label} {field.required && '*'}</Label>
            <Input {...commonProps} type="number" />
            {errors[field.id] && (
              <div className="flex items-center gap-1 text-sm text-destructive mt-1">
                <AlertCircle className="h-4 w-4" />
                {errors[field.id]}
              </div>
            )}
          </div>
        );
      case "date":
        return (
          <div key={field.id}>
            <Label htmlFor={`field-${field.id}`}>{field.label} {field.required && '*'}</Label>
            <Input {...commonProps} type="date" />
            {errors[field.id] && (
              <div className="flex items-center gap-1 text-sm text-destructive mt-1">
                <AlertCircle className="h-4 w-4" />
                {errors[field.id]}
              </div>
            )}
          </div>
        );
      case "boolean":
        return (
          <div key={field.id} className="flex items-center space-x-2">
            <Checkbox
              id={`field-${field.id}`}
              checked={formData[field.id] === true || formData[field.id] === "true"}
              onCheckedChange={(checked) => setFormData({ ...formData, [field.id]: checked })}
              disabled={submission?.locked}
            />
            <Label htmlFor={`field-${field.id}`}>{field.label} {field.required && '*'}</Label>
            {errors[field.id] && (
              <div className="flex items-center gap-1 text-sm text-destructive mt-1">
                <AlertCircle className="h-4 w-4" />
                {errors[field.id]}
              </div>
            )}
          </div>
        );
      case "select":
        return (
          <div key={field.id}>
            <Label htmlFor={`field-${field.id}`}>{field.label} {field.required && '*'}</Label>
            <Select
              value={formData[field.id] || ""}
              onValueChange={(value) => setFormData({ ...formData, [field.id]: value })}
              disabled={submission?.locked}
            >
              <SelectTrigger className={errors[field.id] ? 'border-destructive' : ''}>
                <SelectValue placeholder="Select an option" />
              </SelectTrigger>
              <SelectContent>
                {field.options?.map((option) => (
                  <SelectItem key={option} value={option}>{option}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors[field.id] && (
              <div className="flex items-center gap-1 text-sm text-destructive mt-1">
                <AlertCircle className="h-4 w-4" />
                {errors[field.id]}
              </div>
            )}
          </div>
        );
      default:
        return null;
    }
  };

  if (formId && selectedForm) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate("/forms")}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-foreground">{selectedForm.title}</h1>
            <p className="text-muted-foreground mt-2">{selectedForm.description}</p>
          </div>
        </div>

        <Card className="card-elevated">
          <CardHeader>
            <CardTitle>Form Submission</CardTitle>
            <CardDescription>
              {formStatus && (
                <>
                  {formStatus.is_locked ? (
                    <span className="text-destructive">Form is locked (deadline passed)</span>
                  ) : (
                    <>
                      Deadline: {new Date(formStatus.deadline).toLocaleString()} (
                      {formStatus.time_remaining_seconds > 0
                        ? `${formatDistanceToNow(new Date(formStatus.deadline), { addSuffix: true })}`
                        : "Deadline reached"})
                    </>
                  )}
                  {lastSaved && (
                    <span className="ml-4 text-sm text-muted-foreground">
                      Last saved: {formatDistanceToNow(lastSaved, { addSuffix: true })}
                    </span>
                  )}
                </>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {selectedForm.fields.sort((a, b) => a.position - b.position).map(renderField)}
              <div className="flex gap-4">
                <Button
                  type="submit"
                  disabled={isSaving || submission?.locked}
                  className="btn-primary"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {isSaving ? "Saving..." : submission ? "Update Submission" : "Submit Form"}
                </Button>
                {submission && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleDownload}
                    disabled={!submission}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download PDF
                  </Button>
                )}
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate("/forms")}
                  disabled={isSaving}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-foreground">Available Forms</h1>
      <p className="text-muted-foreground">View and register for available forms</p>
      {isLoading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : forms.length === 0 ? (
        <p className="text-muted-foreground">No forms available at this time</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {forms.map((form) => (
            <Card key={form.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle>{form.title}</CardTitle>
                <CardDescription>{form.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <p className="text-sm">
                    <strong>Opens:</strong> {new Date(form.open_date).toLocaleString()}
                  </p>
                  <p className="text-sm">
                    <strong>Deadline:</strong> {new Date(form.close_date).toLocaleString()}
                  </p>
                  <p className="text-sm">
                    <strong>Status:</strong>{" "}
                    <span className={form.status === "open" ? "text-green-600" : "text-red-600"}>
                      {form.status}
                    </span>
                  </p>
                  <Button
                    onClick={() => navigate(`/forms/${form.id}`)}
                    disabled={form.status !== "open"}
                    className="w-full mt-4"
                  >
                    {form.status === "open" ? "Register Now" : "Form Closed"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default StudentFormsPage;