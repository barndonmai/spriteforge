import type { ChangeEvent, FormEvent } from "react";

import type { JobMode } from "@/lib/types";

interface JobFormProps {
  file: File | null;
  mode: JobMode;
  targetSize: number;
  notes: string;
  fileError: string | null;
  isSubmitting: boolean;
  onFileChange: (file: File | null) => void;
  onFileValidationError: (message: string | null) => void;
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

const fieldClassName =
  "w-full rounded-3xl border border-stone-200 bg-white/90 px-4 py-3 text-stone-900 shadow-sm outline-none transition focus:border-forge-500 focus:ring-4 focus:ring-forge-500/10";

export function JobForm(props: JobFormProps) {
  const handleFileInput = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] ?? null;
    if (!nextFile) {
      props.onFileValidationError(null);
      props.onFileChange(null);
      return;
    }

    const allowedTypes = new Set(["image/png", "image/jpeg"]);
    const lowerName = nextFile.name.toLowerCase();
    const hasAllowedExtension = lowerName.endsWith(".png") || lowerName.endsWith(".jpg") || lowerName.endsWith(".jpeg");

    if (!allowedTypes.has(nextFile.type) || !hasAllowedExtension) {
      event.target.value = "";
      props.onFileValidationError("Only .png, .jpg, and .jpeg files are supported.");
      props.onFileChange(null);
      return;
    }

    props.onFileValidationError(null);
    props.onFileChange(nextFile);
  };

  return (
    <form
      className="rounded-4xl border border-white/70 bg-white/75 p-6 shadow-panel backdrop-blur md:p-7"
      onSubmit={props.onSubmit}
    >
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-stone-950">Create Job</h2>
          <p className="mt-2 text-sm leading-6 text-stone-600">
            Upload one reference image, choose the generation mode, and let the worker produce the final asset package.
          </p>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-stone-900" htmlFor="reference-image">
            Reference Image
          </label>
          <input
            id="reference-image"
            className={fieldClassName}
            type="file"
            accept=".png,.jpg,.jpeg,image/png,image/jpeg"
            onChange={handleFileInput}
            required
          />
          <p className="text-sm text-stone-500">{props.file ? props.file.name : "PNG and JPEG only."}</p>
          {props.fileError ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{props.fileError}</div>
          ) : null}
        </div>

        <fieldset className="space-y-2 border-0 p-0">
          <legend className="text-sm font-semibold text-stone-900">Mode</legend>
          <div className="grid gap-3 sm:grid-cols-3">
            {modeOptions.map((option) => (
              <label className="block cursor-pointer" key={option.value}>
                <input
                  checked={props.mode === option.value}
                  name="mode"
                  className="peer sr-only"
                  type="radio"
                  value={option.value}
                  onChange={() => props.onModeChange(option.value)}
                />
                <span className="flex min-h-32 w-full flex-col rounded-3xl border border-stone-200 bg-white/85 p-4 transition duration-150 peer-checked:border-forge-500 peer-checked:bg-forge-500/10 peer-checked:shadow-sm">
                  <span className="text-lg font-semibold text-stone-950">{option.title}</span>
                  <span className="mt-2 text-sm leading-6 text-stone-600">{option.copy}</span>
                </span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-stone-900" htmlFor="target-size">
            Target Size
          </label>
          <select
            id="target-size"
            className={fieldClassName}
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

        <div className="space-y-2">
          <label className="text-sm font-semibold text-stone-900" htmlFor="notes">
            Notes
          </label>
          <textarea
            id="notes"
            className={`${fieldClassName} min-h-36 resize-y`}
            placeholder="Optional art notes. Example: red hood, silver shoulder armor, emerald cape."
            value={props.notes}
            onChange={(event) => props.onNotesChange(event.target.value)}
          />
        </div>

        <div className="flex items-center gap-3">
        <button
          className="inline-flex min-h-14 items-center justify-center rounded-full bg-forge-500 px-6 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-forge-600 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
          disabled={props.isSubmitting || !props.file}
          type="submit"
        >
          {props.isSubmitting ? "Submitting..." : "Create Sprite Job"}
        </button>
        </div>
      </div>
    </form>
  );
}
