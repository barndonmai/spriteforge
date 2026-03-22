import type { JobStatusResponse } from "@/lib/types";

interface JobStatusCardProps {
  job: JobStatusResponse;
}

export function JobStatusCard({ job }: JobStatusCardProps) {
  return (
    <section className="panel panel-content stack">
      <div className={`status-badge ${job.status}`}>{job.status}</div>
      <div>
        <h2 style={{ margin: "8px 0 6px", fontSize: "1.35rem" }}>Job Status</h2>
        <p className="muted-copy" style={{ margin: 0 }}>
          Track the worker pipeline and review the resolved mode once classification has completed.
        </p>
      </div>

      <div className="detail-grid">
        <div className="detail-card">
          <p className="detail-label">Job ID</p>
          <p className="detail-value">{job.job_id}</p>
        </div>
        <div className="detail-card">
          <p className="detail-label">Stage</p>
          <p className="detail-value">{job.stage ?? "ready"}</p>
        </div>
        <div className="detail-card">
          <p className="detail-label">Requested Mode</p>
          <p className="detail-value">{job.requested_mode}</p>
        </div>
        <div className="detail-card">
          <p className="detail-label">Resolved Mode</p>
          <p className="detail-value">{job.resolved_mode ?? "pending"}</p>
        </div>
      </div>

      {job.error ? <div className="error-banner">{job.error}</div> : null}
    </section>
  );
}

