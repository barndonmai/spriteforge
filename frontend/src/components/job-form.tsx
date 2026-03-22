import type { ChangeEvent, FormEvent } from "react";

import type { JobMode } from "@/lib/types";

interface JobFormProps {
  file: File | null;
  mode: JobMode;
  targetSize: number;
  notes: string;
  isSubmitting: boolean;
  onFileChange: (file: File | null) => void;
  onModeChange: (mode: JobMode) => void;
  onTargetSizeChange: (size: number) => void;
  onNotesChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}

const modeOptions: Array<{ value: JobMode; title: string; copy: string }> = [
  { value: "character", title: "Character", copy: "Generate an 8-direction sprite set." },
  { value: "object", title: "Object", copy: "Generate a single sprite output." },
  { value: "auto", title: "Auto", copy: "Classify first, then run the correct flow." },
];

export function JobForm(props: JobFormProps) {
  const handleFileInput = (event: ChangeEvent<HTMLInputElement>) => {
    props.onFileChange(event.target.files?.[0] ?? null);
  };

  return (
    <form className="panel panel-content stack" onSubmit={props.onSubmit}>
      <div className="stack">
        <div>
          <h2 style={{ margin: 0, fontSize: "1.35rem" }}>Create Job</h2>
          <p className="muted-copy" style={{ marginBottom: 0 }}>
            Upload one reference image, choose the generation mode, and let the worker produce the final asset package.
          </p>
        </div>

        <div className="field">
          <label htmlFor="reference-image">Reference Image</label>
          <input
            id="reference-image"
            className="file-input"
            type="file"
            accept="image/*"
            onChange={handleFileInput}
            required
          />
          <span className="muted-copy">{props.file ? props.file.name : "PNG, JPG, WEBP, or similar image formats."}</span>
        </div>

        <fieldset className="field" style={{ border: 0, padding: 0, margin: 0 }}>
          <legend>Mode</legend>
          <div className="radio-grid">
            {modeOptions.map((option) => (
              <label className="radio-card" key={option.value}>
                <input
                  checked={props.mode === option.value}
                  name="mode"
                  type="radio"
                  value={option.value}
                  onChange={() => props.onModeChange(option.value)}
                />
                <span className="radio-surface">
                  <span className="radio-title">{option.title}</span>
                  <span className="radio-copy">{option.copy}</span>
                </span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="field">
          <label htmlFor="target-size">Target Size</label>
          <select
            id="target-size"
            className="select"
            value={props.targetSize}
            onChange={(event) => props.onTargetSizeChange(Number(event.target.value))}
          >
            {[32, 48, 64, 96, 128].map((size) => (
              <option key={size} value={size}>
                {size}x{size}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            className="textarea"
            placeholder="Optional art notes. Example: red hood, silver shoulder armor, emerald cape."
            value={props.notes}
            onChange={(event) => props.onNotesChange(event.target.value)}
          />
        </div>
      </div>

      <div className="button-row">
        <button className="button button-primary" disabled={props.isSubmitting || !props.file} type="submit">
          {props.isSubmitting ? "Submitting..." : "Create Sprite Job"}
        </button>
      </div>
    </form>
  );
}

