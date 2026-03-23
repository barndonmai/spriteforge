import { useRef, useState } from "react";
import type { ChangeEvent, ClipboardEvent, DragEvent, FormEvent } from "react";

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
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isPastingFromClipboard, setIsPastingFromClipboard] = useState(false);

  const applyValidatedFile = (nextFile: File | null) => {
    if (!nextFile) {
      props.onFileValidationError(null);
      props.onFileChange(null);
      return false;
    }

    const allowedTypes = new Set(["image/png", "image/jpeg"]);
    const lowerName = nextFile.name.toLowerCase();
    const hasAllowedExtension = lowerName.endsWith(".png") || lowerName.endsWith(".jpg") || lowerName.endsWith(".jpeg");

    if (!allowedTypes.has(nextFile.type) || !hasAllowedExtension) {
      props.onFileValidationError("Only .png, .jpg, and .jpeg files are supported.");
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
    if (!("clipboard" in navigator) || !("read" in navigator.clipboard)) {
      props.onFileValidationError("Clipboard image paste is not available in this browser.");
      return;
    }

    try {
      setIsPastingFromClipboard(true);
      const clipboardItems = await navigator.clipboard.read();
      let sawAnyImage = false;

      for (const item of clipboardItems) {
        const availableImageType = item.types.find((type) => type.startsWith("image/"));
        if (availableImageType) {
          sawAnyImage = true;
        }

        const imageType = item.types.find((type) => type === "image/png" || type === "image/jpeg");
        if (!imageType) {
          continue;
        }

        const blob = await item.getType(imageType);
        const extension = imageType === "image/png" ? "png" : "jpg";
        const nextFile = new File([blob], `clipboard-image.${extension}`, { type: imageType });
        applyValidatedFile(nextFile);
        return;
      }

      if (sawAnyImage) {
        props.onFileValidationError("Clipboard image is not supported. Only .png, .jpg, and .jpeg files are supported.");
        return;
      }

      props.onFileValidationError("No image was found in the clipboard.");
    } catch {
      props.onFileValidationError("Clipboard access failed. Try allowing clipboard permissions or paste directly into the upload area.");
    } finally {
      setIsPastingFromClipboard(false);
    }
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
          <div
            className={`rounded-3xl border-2 border-dashed bg-white/90 p-4 shadow-sm outline-none transition ${
              isDragging
                ? "border-forge-500 bg-forge-500/5 ring-4 ring-forge-500/10"
                : "border-stone-200 hover:border-forge-300"
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
                <p className="text-sm font-semibold text-stone-900">Drop an image here, browse, or paste from clipboard.</p>
                <p className="text-sm leading-6 text-stone-500">
                  PNG and JPEG only. You can also focus this upload area and press paste after copying an image.
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  className="inline-flex min-h-11 items-center justify-center rounded-full border border-stone-200 bg-white px-4 py-2 text-sm font-semibold text-stone-900 transition hover:border-forge-400 hover:text-forge-700"
                  type="button"
                  onClick={() => inputRef.current?.click()}
                >
                  Browse Files
                </button>
                <button
                  className="inline-flex min-h-11 items-center justify-center rounded-full border border-stone-200 bg-white px-4 py-2 text-sm font-semibold text-stone-900 transition hover:border-forge-400 hover:text-forge-700 disabled:cursor-not-allowed disabled:opacity-60"
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
          <p className="text-sm text-stone-500">{props.file ? `${props.file.name} · ${(props.file.size / 1024).toFixed(0)} KB` : "PNG and JPEG only."}</p>
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
