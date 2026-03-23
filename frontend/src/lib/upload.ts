const SUPPORTED_IMAGE_TYPES = new Set(["image/png", "image/jpeg"]);
const SUPPORTED_IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"];

export const UNSUPPORTED_IMAGE_MESSAGE = "Only .png, .jpg, and .jpeg files are supported.";

export function validateSupportedImageFile(file: File | null): string | null {
  if (!file) {
    return null;
  }

  const lowerName = file.name.toLowerCase();
  const hasAllowedExtension = SUPPORTED_IMAGE_EXTENSIONS.some((extension) => lowerName.endsWith(extension));
  if (!SUPPORTED_IMAGE_TYPES.has(file.type) || !hasAllowedExtension) {
    return UNSUPPORTED_IMAGE_MESSAGE;
  }

  return null;
}

export async function readClipboardImageFile(): Promise<{ file: File | null; error: string | null }> {
  if (!("clipboard" in navigator) || !("read" in navigator.clipboard)) {
    return { file: null, error: "Clipboard image paste is not available in this browser." };
  }

  try {
    const clipboardItems = await navigator.clipboard.read();
    let sawAnyImage = false;

    for (const item of clipboardItems) {
      const availableImageType = item.types.find((type) => type.startsWith("image/"));
      if (availableImageType) {
        sawAnyImage = true;
      }

      const imageType = item.types.find((type) => SUPPORTED_IMAGE_TYPES.has(type));
      if (!imageType) {
        continue;
      }

      const blob = await item.getType(imageType);
      const extension = imageType === "image/png" ? "png" : "jpg";
      const file = new File([blob], `clipboard-image.${extension}`, { type: imageType });
      return { file, error: null };
    }

    if (sawAnyImage) {
      return { file: null, error: "Clipboard image is not supported. Only .png, .jpg, and .jpeg files are supported." };
    }

    return { file: null, error: "No image was found in the clipboard." };
  } catch {
    return { file: null, error: "Clipboard access failed. Try allowing clipboard permissions or paste directly into the upload area." };
  }
}
