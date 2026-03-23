import { useRef, useState } from "react";
import type { ChangeEvent, ClipboardEvent, DragEvent, FormEvent } from "react";

import type { JobMode } from "@/lib/types";
import { readClipboardImageFile, validateSupportedImageFile } from "@/lib/upload";

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
  "w-full rounded-3xl border border-white/10 bg-white/[0.08] px-4 py-3 text-white shadow-sm outline-none transition placeholder:text-white/35 focus:border-amber-200/50 focus:ring-4 focus:ring-amber-200/10";

export function JobForm(props: JobFormProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isPastingFromClipboard, setIsPastingFromClipboard] = useState(false);

  const applyValidatedFile = (nextFile: File | null) => {
    if (!nextFile) {
      props.onFileValidationError(null);
      props.onFileChange(null);
      return false;
    }

    const validationError = validateSupportedImageFile(nextFile);
    if (validationError) {
      props.onFileValidationError(validationError);
      props.onFileChange(null);
      return false;
    }

    props.onFileValidationError(null);
    props.onFileChange(nextFile);
    return true;
  };

  const handleFileInput = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] ?? null;
    const isValid = applyValidatedFile(nextFile);
    if (!isValid) {
      event.target.value = "";
    }
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const nextFile = event.dataTransfer.files?.[0] ?? null;
    applyValidatedFile(nextFile);
  };

  const handlePaste = (event: ClipboardEvent<HTMLDivElement>) => {
    const nextFile = event.clipboardData.files?.[0] ?? null;
    if (!nextFile) {
      return;
    }

    event.preventDefault();
    applyValidatedFile(nextFile);
  };

  const handlePasteFromClipboard = async () => {
    try {
      setIsPastingFromClipboard(true);
      const { file: clipboardFile, error: clipboardError } = await readClipboardImageFile();
      if (clipboardError) {
        props.onFileValidationError(clipboardError);
        return;
      }

      applyValidatedFile(clipboardFile);
    } finally {
      setIsPastingFromClipboard(false);
    }
  };

  return (
    <form
      className="surface-panel p-6 md:p-7"
      onSubmit={props.onSubmit}
    >
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Create Job</h2>
          <p className="mt-2 text-sm leading-6 text-white/68">
            Upload one reference image, choose the generation mode, and let the worker produce the final asset package.
          </p>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-white" htmlFor="reference-image">
            Reference Image
          </label>
          <div
            className={`rounded-3xl border-2 border-dashed bg-white/[0.05] p-4 shadow-sm outline-none transition ${
              isDragging
                ? "border-amber-200/70 bg-amber-100/10 ring-4 ring-amber-100/10"
                : "border-white/14 hover:border-amber-200/35"
            }`}
            tabIndex={0}
            onDragEnter={() => setIsDragging(true)}
            onDragLeave={() => setIsDragging(false)}
            onDragOver={(event) => {
              event.preventDefault();
              if (!isDragging) {
                setIsDragging(true);
              }
            }}
            onDrop={handleDrop}
            onPaste={handlePaste}
          >
            <input
              ref={inputRef}
              id="reference-image"
              className="sr-only"
              type="file"
              accept=".png,.jpg,.jpeg,image/png,image/jpeg"
              onChange={handleFileInput}
            />
            <div className="space-y-4">
              <div className="space-y-2">
                <p className="text-sm font-semibold text-white">Drop an image here, browse, or paste from clipboard.</p>
                <p className="text-sm leading-6 text-white/55">
                  PNG and JPEG only. You can also focus this upload area and press paste after copying an image.
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  className="ghost-button min-h-11 px-4 py-2"
                  type="button"
                  onClick={() => inputRef.current?.click()}
                >
                  Browse Files
                </button>
                <button
                  className="ghost-button min-h-11 px-4 py-2 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={isPastingFromClipboard}
                  type="button"
                  onClick={() => {
                    void handlePasteFromClipboard();
                  }}
                >
                  Paste From Clipboard
                </button>
              </div>
            </div>
          </div>
          <p className="text-sm text-white/52">
            {props.file ? `${props.file.name} · ${(props.file.size / 1024).toFixed(0)} KB` : "PNG and JPEG only."}
          </p>
          {props.fileError ? (
            <div className="rounded-2xl border border-red-300/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">{props.fileError}</div>
          ) : null}
        </div>

        <fieldset className="space-y-2 border-0 p-0">
          <legend className="text-sm font-semibold text-white">Mode</legend>
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
                <span className="flex min-h-32 w-full flex-col rounded-3xl border border-white/10 bg-white/[0.06] p-4 transition duration-150 peer-checked:border-amber-200/40 peer-checked:bg-amber-100/10 peer-checked:shadow-sm">
                  <span className="text-lg font-semibold text-white">{option.title}</span>
                  <span className="mt-2 text-sm leading-6 text-white/60">{option.copy}</span>
                </span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-white" htmlFor="target-size">
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
          <label className="text-sm font-semibold text-white" htmlFor="notes">
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
          <button className="accent-button min-h-14" disabled={props.isSubmitting || !props.file} type="submit">
            {props.isSubmitting ? "Submitting..." : "Create Sprite Job"}
          </button>
        </div>
      </div>
    </form>
  );
}
