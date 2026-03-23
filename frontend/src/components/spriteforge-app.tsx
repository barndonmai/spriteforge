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
  const [isPolling, setIsPolling] = useState<boolean>(false);
  const [isLoadingResults, setIsLoadingResults] = useState<boolean>(false);
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [results, setResults] = useState<JobResultsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!job || job.status === "completed" || job.status === "failed") {
      setIsPolling(false);
      return;
    }

    setIsPolling(true);

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
      setIsLoadingResults(false);
      return;
    }

    const loadResults = async () => {
      try {
        setIsLoadingResults(true);
        const nextResults = await getResults(job.job_id);
        setResults(nextResults);
      } catch (nextError) {
        setError(nextError instanceof Error ? nextError.message : "Failed to fetch completed job results.");
      } finally {
        setIsLoadingResults(false);
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
    setFileError(null);
    setResults(null);
    setJob(null);
    setIsSubmitting(true);
    setIsLoadingResults(false);

    try {
      const createdJob = await createJob({
        file,
        mode,
        targetSize,
        notes,
      });

      const fullJob = await getJob(createdJob.job_id);
      setJob(fullJob);
      if (fullJob.status === "failed" && fullJob.error) {
        setError(fullJob.error);
      }
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
    <main className="mx-auto min-h-screen max-w-7xl px-4 py-10 sm:px-6 lg:px-8 lg:py-14">
      <header className="mb-8 space-y-4 lg:mb-10">
        <span className="inline-flex w-fit rounded-full border border-stone-200 bg-white/70 px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-stone-600 shadow-sm backdrop-blur">
          SpriteForge v1
        </span>
        <div className="space-y-4">
          <h1 className="max-w-4xl text-4xl font-bold tracking-[-0.05em] text-stone-950 sm:text-5xl lg:text-6xl">
            Game-ready pixel assets, with a clean local pipeline.
          </h1>
          <p className="max-w-3xl text-base leading-7 text-stone-600 sm:text-lg">
            Upload a reference, choose character, object, or auto, and let the FastAPI plus Celery pipeline produce a
            manifest-backed sprite package with mock generation you can test today.
          </p>
        </div>
      </header>

      <div className="grid items-start gap-6 lg:grid-cols-[420px_minmax(0,1fr)]">
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

        <div className="space-y-6">
          {isSubmitting ? (
            <div className="rounded-2xl border border-forge-500/20 bg-forge-500/10 px-4 py-3 text-sm text-forge-700">
              Uploading your reference and creating the job...
            </div>
          ) : null}
          {isPolling && job ? (
            <div className="rounded-2xl border border-forge-500/20 bg-forge-500/10 px-4 py-3 text-sm text-forge-700">
              Worker is running{job.stage ? `: ${job.stage.replaceAll("_", " ")}` : "..."}
            </div>
          ) : null}
          {isLoadingResults ? (
            <div className="rounded-2xl border border-forge-500/20 bg-forge-500/10 px-4 py-3 text-sm text-forge-700">
              Loading completed assets and manifest...
            </div>
          ) : null}
          {error ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
          ) : null}
          {job ? (
            <JobStatusCard job={job} />
          ) : (
            <section className="grid min-h-80 place-content-center gap-2 rounded-4xl border border-dashed border-stone-300 bg-white/50 p-8 text-center shadow-panel backdrop-blur">
              <h2 className="text-2xl font-bold tracking-tight text-stone-950">No job running yet</h2>
              <p className="max-w-lg text-sm leading-6 text-stone-600">
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
