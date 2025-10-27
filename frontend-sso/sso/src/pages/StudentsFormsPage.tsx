import React, { useState, useEffect, useCallback } from "react";

const API_BASE_URL = "https://backend.jkusa.org";

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
  const [view, setView] = useState<"list" | "detail">("list");
  const [forms, setForms] = useState<Form[]>([]);
  const [selectedForm, setSelectedForm] = useState<Form | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [formStatus, setFormStatus] = useState<FormStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const makeAuthenticatedRequest = async (
    url: string,
    options?: RequestInit
  ) => {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
      });
      return response;
    } catch (error) {
      throw error;
    }
  };

  const formatDistanceToNow = (date: Date) => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return "now";
  };

  // Fetch forms list
  useEffect(() => {
    if (view !== "list") return;
    const fetchForms = async () => {
      setIsLoading(true);
      try {
        const response = await makeAuthenticatedRequest(
          `${API_BASE_URL}/registrations/forms?limit=50`
        );
        if (response.ok) {
          const data = await response.json();
          const formsArray = Array.isArray(data) ? data : data.items || [];
          setForms(
            formsArray.sort(
              (a: Form, b: Form) =>
                new Date(b.open_date).getTime() -
                new Date(a.open_date).getTime()
            )
          );
        } else {
          throw new Error("Failed to load forms");
        }
      } catch (error) {
        setToastMessage((error as Error).message);
        setTimeout(() => setToastMessage(null), 3000);
      } finally {
        setIsLoading(false);
      }
    };
    fetchForms();
  }, [view]);

  const handleSelectForm = async (formId: number) => {
    setIsLoading(true);
    try {
      const [formResponse, statusResponse, submissionResponse] =
        await Promise.all([
          makeAuthenticatedRequest(
            `${API_BASE_URL}/registrations/forms/${formId}`
          ),
          makeAuthenticatedRequest(
            `${API_BASE_URL}/registrations/forms/${formId}/status`
          ),
          makeAuthenticatedRequest(
            `${API_BASE_URL}/registrations/forms/${formId}/submission`
          ).catch(() => null),
        ]);

      if (formResponse.ok) {
        const form = await formResponse.json();
        setSelectedForm(form);
        setFormData(
          form.fields.reduce(
            (acc: any, field: Field) => ({
              ...acc,
              [field.id]: field.default_value || "",
            }),
            {}
          )
        );
      } else {
        throw new Error("Failed to load form");
      }

      if (statusResponse.ok) {
        setFormStatus(await statusResponse.json());
      }

      if (submissionResponse && submissionResponse.ok) {
        setSubmission(await submissionResponse.json());
      }

      setView("detail");
    } catch (error) {
      setToastMessage((error as Error).message);
      setTimeout(() => setToastMessage(null), 3000);
    } finally {
      setIsLoading(false);
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    if (selectedForm) {
      selectedForm.fields.forEach((field) => {
        if (field.required && !formData[field.id]) {
          newErrors[field.id] = `${field.label} is required`;
        }
        if (
          field.field_type === "email" &&
          formData[field.id] &&
          !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData[field.id])
        ) {
          newErrors[field.id] = "Invalid email format";
        }
        if (
          field.field_type === "number" &&
          formData[field.id] &&
          isNaN(Number(formData[field.id]))
        ) {
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
      const method = submission ? "PUT" : "POST";
      const response = await makeAuthenticatedRequest(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (response.ok) {
        const data = await response.json();
        setSubmission(data);
        setLastSaved(new Date());
        setToastMessage("Progress saved");
        setTimeout(() => setToastMessage(null), 3000);
      } else {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `Failed to ${submission ? "update" : "submit"} form`
        );
      }
    } catch (error) {
      setToastMessage((error as Error).message);
      setTimeout(() => setToastMessage(null), 3000);
    } finally {
      setIsSaving(false);
    }
  }, [selectedForm, formData, submission]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) {
      setToastMessage("Please fix the errors below");
      setTimeout(() => setToastMessage(null), 3000);
      return;
    }
    handleSave();
    setTimeout(() => setView("list"), 1500);
  };

  const handleDownload = async () => {
    if (!submission || !selectedForm) return;
    try {
      const response = await makeAuthenticatedRequest(
        `${API_BASE_URL}/registrations/forms/${selectedForm.id}/submissions/export?format=pdf`,
        { method: "GET" }
      );
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `submission_${submission.id}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        throw new Error("Failed to download submission");
      }
    } catch (error) {
      setToastMessage((error as Error).message);
      setTimeout(() => setToastMessage(null), 3000);
    }
  };

  const isFieldVisible = (field: Field) => {
    if (!field.conditions.length) return true;
    return field.conditions.every((condition) => {
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

    const isDisabled =
      submission?.locked ||
      field.label.toLowerCase().includes("name") ||
      field.label.toLowerCase().includes("email") ||
      field.label.toLowerCase().includes("registration") ||
      field.label.toLowerCase().includes("college") ||
      field.label.toLowerCase().includes("school");

    const inputClass = `w-full px-4 py-2 bg-white border rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-500 ${
      errors[field.id] ? "border-red-500" : "border-gray-300"
    }`;

    const renderInput = () => {
      switch (field.field_type) {
        case "text":
        case "email":
          return (
            <input
              id={`field-${field.id}`}
              type={field.field_type}
              value={formData[field.id] || ""}
              onChange={(e) =>
                setFormData({ ...formData, [field.id]: e.target.value })
              }
              className={inputClass}
              disabled={isDisabled}
              required={field.required}
            />
          );
        case "textarea":
          return (
            <textarea
              id={`field-${field.id}`}
              value={formData[field.id] || ""}
              onChange={(e) =>
                setFormData({ ...formData, [field.id]: e.target.value })
              }
              className={`${inputClass} resize-none`}
              rows={4}
              disabled={isDisabled}
              required={field.required}
            />
          );
        case "number":
          return (
            <input
              id={`field-${field.id}`}
              type="number"
              value={formData[field.id] || ""}
              onChange={(e) =>
                setFormData({ ...formData, [field.id]: e.target.value })
              }
              className={inputClass}
              disabled={isDisabled}
              required={field.required}
            />
          );
        case "date":
          return (
            <input
              id={`field-${field.id}`}
              type="date"
              value={formData[field.id] || ""}
              onChange={(e) =>
                setFormData({ ...formData, [field.id]: e.target.value })
              }
              className={inputClass}
              disabled={isDisabled}
              required={field.required}
            />
          );
        case "boolean":
          return (
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id={`field-${field.id}`}
                checked={
                  formData[field.id] === true ||
                  formData[field.id] === "true"
                }
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    [field.id]: e.target.checked,
                  })
                }
                disabled={submission?.locked}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
              />
              <label
                htmlFor={`field-${field.id}`}
                className="text-sm font-medium text-gray-900"
              >
                {field.label}
                {field.required && <span className="text-red-600 ml-1">*</span>}
              </label>
            </div>
          );
        case "select":
          return (
            <select
              id={`field-${field.id}`}
              value={formData[field.id] || ""}
              onChange={(e) =>
                setFormData({ ...formData, [field.id]: e.target.value })
              }
              className={inputClass}
              disabled={isDisabled}
              required={field.required}
            >
              <option value="">Select an option</option>
              {field.options?.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          );
        default:
          return null;
      }
    };

    return (
      <div
        key={field.id}
        className={
          field.field_type === "boolean" ? "" : "space-y-2"
        }
      >
        {field.field_type !== "boolean" && (
          <label
            htmlFor={`field-${field.id}`}
            className="block text-sm font-medium text-gray-900"
          >
            {field.label}
            {field.required && <span className="text-red-600 ml-1">*</span>}
          </label>
        )}
        {renderInput()}
        {errors[field.id] && (
          <div className="flex items-center gap-1 text-sm text-red-600">
            <span>⚠️</span>
            {errors[field.id]}
          </div>
        )}
      </div>
    );
  };

  // Detail View
  if (view === "detail" && selectedForm) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-6 lg:py-8">
        {toastMessage && (
          <div className="fixed top-4 right-4 bg-blue-600 text-white px-6 py-3 rounded-lg shadow-lg z-50">
            {toastMessage}
          </div>
        )}

        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => setView("list")}
            className="flex items-center justify-center w-10 h-10 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <span className="text-2xl">←</span>
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {selectedForm.title}
            </h1>
            <p className="text-gray-600 mt-2">{selectedForm.description}</p>
          </div>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 lg:p-8">
          {/* Status Info */}
          {formStatus && (
            <div
              className={`mb-6 p-4 rounded-lg border-l-4 ${
                formStatus.is_locked
                  ? "bg-red-50 border-red-400"
                  : "bg-blue-50 border-blue-400"
              }`}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl mt-0.5">
                  {formStatus.is_locked ? "🔒" : "⏰"}
                </span>
                <div>
                  <p
                    className={`font-medium ${
                      formStatus.is_locked
                        ? "text-red-800"
                        : "text-blue-800"
                    }`}
                  >
                    {formStatus.is_locked
                      ? "Form is locked (deadline passed)"
                      : `Deadline: ${new Date(
                          formStatus.deadline
                        ).toLocaleString()}`}
                  </p>
                  {!formStatus.is_locked && (
                    <p
                      className={`text-sm mt-1 ${
                        formStatus.is_locked ? "text-red-700" : "text-blue-700"
                      }`}
                    >
                      {formatDistanceToNow(new Date(formStatus.deadline))}
                    </p>
                  )}
                  {lastSaved && (
                    <p className="text-xs text-gray-600 mt-2">
                      Last saved: {formatDistanceToNow(lastSaved)}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {selectedForm.fields
              .sort((a, b) => a.position - b.position)
              .map(renderField)}

            {/* Actions */}
            <div className="flex flex-wrap gap-4 pt-6 border-t border-gray-200">
              <button
                type="submit"
                disabled={isSaving || submission?.locked}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-medium rounded-lg transition-colors"
              >
                ✓ {isSaving ? "Saving..." : submission ? "Update" : "Submit"}
              </button>

              {submission && (
                <button
                  type="button"
                  onClick={handleDownload}
                  className="flex items-center gap-2 px-6 py-3 bg-white border border-gray-300 hover:bg-gray-50 text-gray-900 font-medium rounded-lg transition-colors"
                >
                  ⬇ Download PDF
                </button>
              )}

              <button
                type="button"
                onClick={() => setView("list")}
                disabled={isSaving}
                className="flex items-center gap-2 px-6 py-3 bg-white border border-gray-300 hover:bg-gray-50 text-gray-900 font-medium rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // List View
  return (
    <div className="max-w-7xl mx-auto px-4 py-6 lg:py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Available Forms
        </h1>
        <p className="text-gray-600">View and register for available forms</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : forms.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-100">
          <span className="text-5xl mb-4 block">📋</span>
          <p className="text-gray-600">No forms available at this time</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {forms.map((form) => {
            const isOpen = form.status === "open";
            return (
              <div
                key={form.id}
                className="bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md hover:border-gray-200 transition-all"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="text-lg font-bold text-gray-900 flex-1">
                      {form.title}
                    </h3>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ml-2 ${
                        isOpen
                          ? "bg-green-100 text-green-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {form.status}
                    </span>
                  </div>

                  <p className="text-sm text-gray-600 mb-4">
                    {form.description}
                  </p>

                  <div className="space-y-2 mb-6">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <span>📅</span>
                      <span>
                        Opens: {new Date(form.open_date).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <span>⏱️</span>
                      <span>
                        Deadline: {new Date(form.close_date).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleSelectForm(form.id)}
                    disabled={!isOpen}
                    className={`w-full py-2.5 px-4 rounded-lg font-medium transition-colors ${
                      isOpen
                        ? "bg-blue-600 hover:bg-blue-700 text-white"
                        : "bg-gray-100 text-gray-400 cursor-not-allowed"
                    }`}
                  >
                    {isOpen ? "Register Now" : "Form Closed"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default StudentFormsPage;