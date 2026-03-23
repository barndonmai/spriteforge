import { resolveApiUrl } from "@/lib/api";
import { formatTorontoDateTime } from "@/lib/formatters";
import type { JobResultsResponse } from "@/lib/types";

interface ResultsGalleryProps {
  results: JobResultsResponse;
}

export function ResultsGallery({ results }: ResultsGalleryProps) {
  const summaryEntries = Object.entries(results.reference_summary ?? {});
  const completedAtLabel = formatTorontoDateTime(results.completed_at);

  return (
    <section className="rounded-4xl border border-white/70 bg-white/75 p-6 shadow-panel backdrop-blur md:p-7">
      <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-stone-950">Generated Results</h2>
          <p className="mt-2 text-sm leading-6 text-stone-600">
            Preview the finalized assets and download the packaged output bundle.
          </p>
          {completedAtLabel ? (
            <p className="mt-2 text-xs font-medium uppercase tracking-[0.16em] text-stone-500">
              Completed {completedAtLabel}
            </p>
          ) : null}
        </div>

        <a
          className="inline-flex min-h-14 items-center justify-center rounded-full bg-forge-500 px-6 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-forge-600"
          href={resolveApiUrl(results.download_url)}
        >
          Download ZIP
        </a>
      </div>

      {summaryEntries.length > 0 ? (
        <div className="rounded-3xl border border-stone-200 bg-white/85 p-5">
          <h3 className="text-lg font-semibold text-stone-950">Reference Summary</h3>
          <dl className="mt-4 grid gap-4 sm:grid-cols-2">
            {summaryEntries.map(([key, value]) => (
              <div className="space-y-1" key={key}>
                <dt className="text-xs font-medium uppercase tracking-[0.16em] text-stone-500">
                  {key.replaceAll("_", " ")}
                </dt>
                <dd className="text-sm font-medium leading-6 text-stone-800">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {results.outputs.map((asset) => (
          <article className="rounded-3xl border border-stone-200 bg-white/85 p-4" key={asset.filename}>
            <div className="checkerboard grid aspect-square place-items-center rounded-2xl border border-stone-200 bg-white">
              <img
                alt={asset.label}
                className="h-full w-full object-contain p-3 [image-rendering:pixelated]"
                src={resolveApiUrl(asset.url)}
              />
            </div>
            <p className="mt-3 text-sm font-semibold capitalize text-stone-900">{asset.label}</p>
          </article>
        ))}
      </div>
      </div>
    </section>
  );
}
