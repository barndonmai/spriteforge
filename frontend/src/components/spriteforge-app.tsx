"use client";

import { FormEvent, useEffect, useState } from "react";

import { JobForm } from "@/components/job-form";
import { JobStatusCard } from "@/components/job-status-card";
import { ResultsGallery } from "@/components/results-gallery";
import { createJob, getJob, getResults } from "@/lib/api";
import type { JobMode, JobResultsResponse, JobStatusResponse } from "@/lib/types";

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
    <main className="relative overflow-hidden hero-sky">
      <div className="pointer-events-none absolute inset-0 opacity-40 pixel-grid" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[32rem] bg-[radial-gradient(circle_at_top,rgba(255,241,178,0.16),transparent_52%)]" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[28rem] bg-[linear-gradient(180deg,transparent_0%,rgba(18,18,47,0.18)_20%,rgba(12,18,38,0.72)_60%,rgba(7,12,28,0.95)_100%)]" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[26rem] bg-[radial-gradient(circle_at_50%_100%,rgba(96,165,250,0.14),transparent_38%)]" />

      <div className="pointer-events-none absolute inset-x-0 bottom-[24rem] h-56 bg-[radial-gradient(circle_at_50%_50%,rgba(254,205,211,0.25),transparent_44%)] blur-3xl" />

      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[22rem] overflow-hidden">
        <div className="absolute inset-x-[-10%] bottom-36 h-56 rounded-[100%] bg-[#5d357a]/90" />
        <div className="absolute left-[-8%] bottom-28 h-60 w-[42%] rounded-[100%] bg-[#302765]" />
        <div className="absolute left-[18%] bottom-28 h-64 w-[36%] rounded-[100%] bg-[#473184]" />
        <div className="absolute right-[8%] bottom-24 h-72 w-[42%] rounded-[100%] bg-[#6c4cb1]" />
        <div className="absolute left-[-6%] bottom-14 h-52 w-[40%] rounded-[100%] bg-[#17254a]" />
        <div className="absolute left-[24%] bottom-10 h-56 w-[34%] rounded-[100%] bg-[#1f2b58]" />
        <div className="absolute right-[-5%] bottom-12 h-60 w-[44%] rounded-[100%] bg-[#132143]" />
        <div className="absolute inset-x-[-5%] bottom-0 h-28 bg-[#0c1737]" />
        <div className="absolute inset-x-[12%] bottom-0 h-24 rounded-t-[100%] bg-[linear-gradient(180deg,rgba(93,69,157,0.12),rgba(93,69,157,0.42)_60%,transparent)] opacity-70 blur-xl" />
      </div>

      <div className="relative mx-auto min-h-screen max-w-7xl px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
        <header className="surface-pill mb-8 flex items-center justify-between px-5 py-3">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-2xl bg-white/10 text-sm font-bold tracking-[0.18em] text-amber-100 ring-1 ring-white/20">
              SF
            </div>
            <div>
              <p className="text-sm font-semibold tracking-[0.18em] text-white">SpriteForge</p>
              <p className="text-xs uppercase tracking-[0.2em] text-white/60">Local-first pixel asset workshop</p>
            </div>
          </div>
          <div className="hidden items-center gap-3 text-xs uppercase tracking-[0.18em] text-white/60 md:flex">
            <span>Next.js</span>
            <span className="text-white/30">/</span>
            <span>FastAPI</span>
            <span className="text-white/30">/</span>
            <span>Celery</span>
          </div>
        </header>

        <section className="relative mb-10 overflow-hidden rounded-[34px] border border-white/10 bg-[#1b1636]/35 px-6 py-8 shadow-[0_32px_120px_rgba(10,8,28,0.42)] backdrop-blur-sm md:px-8 md:py-10 lg:px-10 lg:py-12">
          <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.08),transparent_28%)]" />
          <div className="relative grid gap-8 lg:grid-cols-[minmax(0,1.2fr)_360px] lg:items-end">
            <div className="max-w-4xl">
              <div className="surface-pill inline-flex w-fit items-center gap-2 px-3 py-1.5 text-xs font-medium uppercase tracking-[0.22em] text-amber-100">
                <span className="h-2 w-2 rounded-full bg-amber-200" />
                SpriteForge v1
              </div>
              <h1 className="mt-6 text-4xl font-bold tracking-[-0.06em] text-white sm:text-5xl lg:text-6xl">
                Turn real-world references into pixel art assets that feel ready for a game world.
              </h1>
              <p className="mt-5 max-w-3xl text-base leading-8 text-white/78 sm:text-lg">
                SpriteForge keeps the workflow lean: upload a reference, run a job, preview the output, and download a
                packaged sprite bundle. It stays local-first, practical, and built for asset iteration instead of
                product bloat.
              </p>

              <div className="mt-8 grid gap-4 md:grid-cols-3">
                <div className="surface-subpanel px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-white/52">Modes</p>
                  <p className="mt-2 text-sm font-semibold text-white">Character, object, auto</p>
                </div>
                <div className="surface-subpanel px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-white/52">Pipeline</p>
                  <p className="mt-2 text-sm font-semibold text-white">Upload, queue, preview, download</p>
                </div>
                <div className="surface-subpanel px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-white/52">Storage</p>
                  <p className="mt-2 text-sm font-semibold text-white">Local files, manifest, ZIP package</p>
                </div>
              </div>
            </div>

            <aside className="surface-panel p-6">
              <div className="space-y-5">
                <div>
                  <p className="text-xs uppercase tracking-[0.18em] text-amber-100/90">Current workflow</p>
                  <h2 className="mt-3 text-2xl font-semibold tracking-tight text-white">
                    One upload, one worker run, one downloadable asset bundle.
                  </h2>
                </div>
                <div className="space-y-3 text-sm leading-7 text-white/74">
                  <p>Drop in a prop or character reference and let the async pipeline take it from there.</p>
                  <p>When the job completes, SpriteForge surfaces the metadata, previews, and final ZIP in one place.</p>
                </div>
                <div className="surface-subpanel p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-white/52">Best for</p>
                  <p className="mt-2 text-sm font-semibold text-white">
                    Props, packaging, simple character tests, and quick iteration on your portfolio game workflow.
                  </p>
                </div>
              </div>
            </aside>
          </div>
        </section>

        <div className="grid items-start gap-6 xl:grid-cols-[440px_minmax(0,1fr)]">
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
              <div className="surface-subpanel border border-amber-200/20 px-4 py-3 text-sm text-amber-50">
                Uploading your reference and creating the job...
              </div>
            ) : null}
            {isPolling && job ? (
              <div className="surface-subpanel border border-amber-200/20 px-4 py-3 text-sm text-amber-50">
                Worker is running{job.stage ? `: ${job.stage.replaceAll("_", " ")}` : "..."}
              </div>
            ) : null}
            {isLoadingResults ? (
              <div className="surface-subpanel border border-amber-200/20 px-4 py-3 text-sm text-amber-50">
                Loading completed assets and manifest...
              </div>
            ) : null}
            {error ? (
              <div className="surface-subpanel border border-red-300/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
                {error}
              </div>
            ) : null}

            {job ? (
              <JobStatusCard job={job} />
            ) : (
              <section className="surface-panel grid min-h-80 place-content-center gap-3 p-8 text-center">
                <h2 className="text-2xl font-bold tracking-tight text-white">No job running yet</h2>
                <p className="mx-auto max-w-lg text-sm leading-7 text-white/68">
                  Submit a reference image to start the pipeline. The status card, preview gallery, and download action
                  will appear here once a run is active.
                </p>
              </section>
            )}

            {results ? <ResultsGallery results={results} /> : null}
          </div>
        </div>
      </div>
    </main>
  );
}
