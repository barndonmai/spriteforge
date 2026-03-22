"use client";

import { FormEvent, useEffect, useState } from "react";

import { createJob, getJob, getResults } from "@/lib/api";
import type { JobMode, JobResultsResponse, JobStatusResponse } from "@/lib/types";
import { JobForm } from "@/components/job-form";
import { JobStatusCard } from "@/components/job-status-card";
import { ResultsGallery } from "@/components/results-gallery";

export function SpriteForgeApp() {
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<JobMode>("auto");
  const [targetSize, setTargetSize] = useState<number>(64);
  const [notes, setNotes] = useState<string>("");
  const [fileError, setFileError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [results, setResults] = useState<JobResultsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!job || job.status === "completed" || job.status === "failed") {
      return;
    }

    const loadJobStatus = async () => {
      try {
        const nextJob = await getJob(job.job_id);
        setJob(nextJob);
      } catch (nextError) {
        setError(nextError instanceof Error ? nextError.message : "Failed to poll job status.");
      }
    };

    void loadJobStatus();
    const intervalId = window.setInterval(loadJobStatus, 3000);
    return () => window.clearInterval(intervalId);
  }, [job]);

  useEffect(() => {
    if (!job || job.status !== "completed" || results) {
      return;
    }

    const loadResults = async () => {
      try {
        const nextResults = await getResults(job.job_id);
        setResults(nextResults);
      } catch (nextError) {
        setError(nextError instanceof Error ? nextError.message : "Failed to fetch completed job results.");
      }
    };

    void loadResults();
  }, [job, results]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) {
      setError("Choose a reference image before submitting.");
      return;
    }

    setError(null);
    setResults(null);
    setJob(null);
    setIsSubmitting(true);

    try {
      const createdJob = await createJob({
        file,
        mode,
        targetSize,
        notes,
      });

      const fullJob = await getJob(createdJob.job_id);
      setJob(fullJob);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Job submission failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileChange = (nextFile: File | null) => {
    setFile(nextFile);
    if (nextFile) {
      setError(null);
    }
  };

  return (
    <main className="page-shell">
      <header className="hero">
        <span className="eyebrow">SpriteForge v1</span>
        <h1>Game-ready pixel assets, with a clean local pipeline.</h1>
        <p>
          Upload a reference, choose character, object, or auto, and let the FastAPI plus Celery pipeline produce a
          manifest-backed sprite package with mock generation you can test today.
        </p>
      </header>

      <div className="layout-grid">
        <JobForm
          file={file}
          mode={mode}
          targetSize={targetSize}
          notes={notes}
          fileError={fileError}
          isSubmitting={isSubmitting}
          onFileChange={handleFileChange}
          onFileValidationError={setFileError}
          onModeChange={setMode}
          onTargetSizeChange={setTargetSize}
          onNotesChange={setNotes}
          onSubmit={handleSubmit}
        />

        <div className="stack">
          {error ? <div className="error-banner">{error}</div> : null}
          {job ? (
            <JobStatusCard job={job} />
          ) : (
            <section className="panel panel-content empty-state">
              <h2 style={{ margin: 0 }}>No job running yet</h2>
              <p style={{ margin: 0 }}>
                Submit a reference image to start the pipeline. The status card, preview gallery, and download action
                will appear here.
              </p>
            </section>
          )}

          {results ? <ResultsGallery results={results} /> : null}
        </div>
      </div>
    </main>
  );
}
