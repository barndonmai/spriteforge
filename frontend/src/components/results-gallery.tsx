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
    <section className="surface-panel p-6 md:p-7">
      <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Generated Results</h2>
          <p className="mt-2 text-sm leading-6 text-white/68">
            Preview the finalized assets and download the packaged output bundle.
          </p>
          {completedAtLabel ? (
            <p className="mt-2 text-xs font-medium uppercase tracking-[0.16em] text-white/48">
              Completed {completedAtLabel}
            </p>
          ) : null}
        </div>

        <a className="accent-button min-h-14" href={resolveApiUrl(results.download_url)}>
          Download ZIP
        </a>
      </div>

      {summaryEntries.length > 0 ? (
        <div className="surface-subpanel p-5">
          <h3 className="text-lg font-semibold text-white">Reference Summary</h3>
          <dl className="mt-4 grid gap-4 sm:grid-cols-2">
            {summaryEntries.map(([key, value]) => (
              <div className="space-y-1" key={key}>
                <dt className="text-xs font-medium uppercase tracking-[0.16em] text-white/48">
                  {key.replaceAll("_", " ")}
                </dt>
                <dd className="text-sm font-medium leading-6 text-white/84">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      ) : null}

      {results.warnings.length > 0 ? (
        <div className="rounded-3xl border border-amber-300/30 bg-amber-300/10 p-5">
          <h3 className="text-lg font-semibold text-amber-50">Output Notes</h3>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-amber-100/92">
            {results.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {results.outputs.map((asset) => (
          <article className="surface-subpanel p-4" key={asset.filename}>
            <div className="checkerboard grid aspect-square place-items-center rounded-2xl border border-white/10 bg-[#120f26]">
              <img
                alt={asset.label}
                className="h-full w-full object-contain p-3 [image-rendering:pixelated]"
                src={resolveApiUrl(asset.url)}
              />
            </div>
            <p className="mt-3 text-sm font-semibold capitalize text-white">{asset.label}</p>
          </article>
        ))}
      </div>
      </div>
    </section>
  );
}
