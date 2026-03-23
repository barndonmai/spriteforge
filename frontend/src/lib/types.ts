export type JobMode = "character" | "object" | "auto";
export type ResolvedMode = "character" | "object";
export type JobStatus = "queued" | "processing" | "completed" | "failed";
export type JobStage =
  | "validating_input"
  | "classifying_mode"
  | "extracting_reference_traits"
  | "generating_assets"
  | "normalizing_assets"
  | "packaging_results"
  | null;

export interface CreateJobResponse {
  job_id: string;
  status: JobStatus;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  stage: JobStage;
  requested_mode: JobMode;
  resolved_mode: ResolvedMode | null;
  target_size: number;
  error: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface ResultAsset {
  filename: string;
  label: string;
  storage_path: string;
  width: number;
  height: number;
  url: string;
}

export interface JobResultsResponse {
  job_id: string;
  status: JobStatus;
  requested_mode: JobMode;
  resolved_mode: ResolvedMode;
  target_size: number;
  provider: string;
  reference_image_path: string;
  reference_summary: Record<string, string> | null;
  manifest_path: string;
  download_url: string;
  completed_at: string | null;
  warnings: string[];
  outputs: ResultAsset[];
}
