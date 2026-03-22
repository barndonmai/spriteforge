import { resolveApiUrl } from "@/lib/api";
import type { JobResultsResponse } from "@/lib/types";

interface ResultsGalleryProps {
  results: JobResultsResponse;
}

export function ResultsGallery({ results }: ResultsGalleryProps) {
  const summaryEntries = Object.entries(results.reference_summary ?? {});

  return (
    <section className="panel panel-content stack">
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: "1.35rem" }}>Generated Results</h2>
          <p className="muted-copy" style={{ marginBottom: 0 }}>
            Preview the finalized assets and download the packaged output bundle.
          </p>
        </div>

        <a className="button button-primary" href={resolveApiUrl(results.download_url)}>
          Download ZIP
        </a>
      </div>

      {summaryEntries.length > 0 ? (
        <div className="summary-card">
          <h3>Reference Summary</h3>
          <dl className="summary-list">
            {summaryEntries.map(([key, value]) => (
              <div className="summary-item" key={key}>
                <dt>{key.replaceAll("_", " ")}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      ) : null}

      <div className="gallery-grid">
        {results.outputs.map((asset) => (
          <article className="sprite-card" key={asset.filename}>
            <div className="sprite-frame">
              <img alt={asset.label} src={resolveApiUrl(asset.url)} />
            </div>
            <p className="sprite-label">{asset.label}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

