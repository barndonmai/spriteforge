import { formatTorontoDateTime } from "@/lib/formatters";
import type { JobStatusResponse } from "@/lib/types";

interface JobStatusCardProps {
  job: JobStatusResponse;
}

const statusClassNames: Record<JobStatusResponse["status"], string> = {
  queued: "bg-amber-200/15 text-amber-50 ring-1 ring-amber-200/20",
  processing: "bg-amber-200/15 text-amber-50 ring-1 ring-amber-200/20",
  completed: "bg-emerald-300/15 text-emerald-50 ring-1 ring-emerald-200/20",
  failed: "bg-red-400/15 text-red-100 ring-1 ring-red-300/25",
};

const stageLabels: Record<Exclude<JobStatusResponse["stage"], null>, string> = {
  validating_input: "Validating input",
  classifying_mode: "Classifying mode",
  extracting_reference_traits: "Extracting reference traits",
  generating_assets: "Generating assets",
  normalizing_assets: "Normalizing assets",
  packaging_results: "Packaging results",
};

export function JobStatusCard({ job }: JobStatusCardProps) {
  const stageLabel = job.stage ? stageLabels[job.stage] : job.status === "completed" ? "Completed" : "Waiting";
  const updatedAtLabel = formatTorontoDateTime(job.updated_at);
  const completedAtLabel = formatTorontoDateTime(job.completed_at);

  return (
    <section className="surface-panel p-6 md:p-7">
      <div className="space-y-5">
      <div className={`inline-flex w-fit rounded-full px-3 py-1.5 text-sm font-semibold capitalize ${statusClassNames[job.status]}`}>
        {job.status}
      </div>
      <div>
        <h2 className="mt-2 text-2xl font-bold tracking-tight text-white">Job Status</h2>
        <p className="mt-2 text-sm leading-6 text-white/68">
          Track the worker pipeline and review the resolved mode once classification has completed.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="surface-subpanel p-4">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-white/48">Job ID</p>
          <p className="mt-2 break-all text-sm font-semibold text-white">{job.job_id}</p>
        </div>
        <div className="surface-subpanel p-4">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-white/48">Stage</p>
          <p className="mt-2 text-sm font-semibold text-white">{stageLabel}</p>
        </div>
        <div className="surface-subpanel p-4">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-white/48">Requested Mode</p>
          <p className="mt-2 text-sm font-semibold capitalize text-white">{job.requested_mode}</p>
        </div>
        <div className="surface-subpanel p-4">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-white/48">Resolved Mode</p>
          <p className="mt-2 text-sm font-semibold capitalize text-white">{job.resolved_mode ?? "pending"}</p>
        </div>
        <div className="surface-subpanel p-4 sm:col-span-2">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-white/48">Last Updated</p>
          <p className="mt-2 text-sm font-semibold text-white">
            {updatedAtLabel ?? "Unknown"}
            {completedAtLabel ? ` · completed ${completedAtLabel}` : ""}
          </p>
        </div>
      </div>

      {job.error ? (
        <div className="rounded-2xl border border-red-300/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">{job.error}</div>
      ) : null}
      </div>
    </section>
  );
}
