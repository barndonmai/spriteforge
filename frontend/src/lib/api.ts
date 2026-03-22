import type { CreateJobResponse, JobResultsResponse, JobStatusResponse, JobMode } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function resolveApiUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  return `${API_BASE_URL}${path}`;
}

export async function createJob(params: {
  file: File;
  mode: JobMode;
  targetSize: number;
  notes: string;
}): Promise<CreateJobResponse> {
  const formData = new FormData();
  formData.append("reference_image", params.file);
  formData.append("mode", params.mode);
  formData.append("target_size", String(params.targetSize));
  formData.append("notes", params.notes);

  const response = await fetch(resolveApiUrl("/api/v1/jobs"), {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Failed to create job.");
  }

  return response.json();
}

export async function getJob(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(resolveApiUrl(`/api/v1/jobs/${jobId}`), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch job status.");
  }

  return response.json();
}

export async function getResults(jobId: string): Promise<JobResultsResponse> {
  const response = await fetch(resolveApiUrl(`/api/v1/jobs/${jobId}/results`), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch job results.");
  }

  return response.json();
}

