import type { JobStatusResponse } from "@/lib/types";

interface JobStatusCardProps {
  job: JobStatusResponse;
}

const statusClassNames: Record<JobStatusResponse["status"], string> = {
  queued: "bg-forge-500/10 text-forge-700 ring-1 ring-forge-500/20",
  processing: "bg-forge-500/10 text-forge-700 ring-1 ring-forge-500/20",
  completed: "bg-emerald-500/10 text-emerald-700 ring-1 ring-emerald-500/20",
  failed: "bg-red-500/10 text-red-700 ring-1 ring-red-500/20",
};

export function JobStatusCard({ job }: JobStatusCardProps) {
  return (
    <section className="rounded-4xl border border-white/70 bg-white/75 p-6 shadow-panel backdrop-blur md:p-7">
      <div className="space-y-5">
      <div className={`inline-flex w-fit rounded-full px-3 py-1.5 text-sm font-semibold capitalize ${statusClassNames[job.status]}`}>
        {job.status}
      </div>
      <div>
        <h2 className="mt-2 text-2xl font-bold tracking-tight text-stone-950">Job Status</h2>
        <p className="mt-2 text-sm leading-6 text-stone-600">
          Track the worker pipeline and review the resolved mode once classification has completed.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-3xl border border-stone-200 bg-white/85 p-4">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-stone-500">Job ID</p>
          <p className="mt-2 break-all text-sm font-semibold text-stone-950">{job.job_id}</p>
        </div>
        <div className="rounded-3xl border border-stone-200 bg-white/85 p-4">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-stone-500">Stage</p>
          <p className="mt-2 text-sm font-semibold capitalize text-stone-950">{job.stage ?? "ready"}</p>
        </div>
        <div className="rounded-3xl border border-stone-200 bg-white/85 p-4">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-stone-500">Requested Mode</p>
          <p className="mt-2 text-sm font-semibold capitalize text-stone-950">{job.requested_mode}</p>
        </div>
        <div className="rounded-3xl border border-stone-200 bg-white/85 p-4">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-stone-500">Resolved Mode</p>
          <p className="mt-2 text-sm font-semibold capitalize text-stone-950">{job.resolved_mode ?? "pending"}</p>
        </div>
      </div>

      {job.error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{job.error}</div>
      ) : null}
      </div>
    </section>
  );
}
