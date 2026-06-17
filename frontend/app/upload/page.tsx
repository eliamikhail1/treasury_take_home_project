"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type UploadMode = "single" | "batch";

export default function UploadPage() {
  const router = useRouter();

  const [mode, setMode] = useState<UploadMode>("single");
  const [singleImage, setSingleImage] = useState<File | null>(null);
  const [batchImages, setBatchImages] = useState<File[]>([]);
  const [spreadsheet, setSpreadsheet] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  async function submitSingle(form: HTMLFormElement) {
    if (!singleImage) {
      alert("Please upload one label image.");
      return;
    }

    const formData = new FormData();

    const getValue = (name: string) => {
      const element = form.elements.namedItem(name) as
        | HTMLInputElement
        | HTMLTextAreaElement
        | null;

      return element?.value ?? "";
    };

    formData.append("image", singleImage);
    formData.append("brandName", getValue("brandName"));
    formData.append("className", getValue("className"));
    formData.append("alcoholContent", getValue("alcoholContent"));
    formData.append("netContents", getValue("netContents"));
    formData.append("address", getValue("address"));
    formData.append("importOrigin", getValue("importOrigin"));
    formData.append("healthWarning", getValue("healthWarning"));

    const response = await fetch("http://localhost:8000/single-label-check", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    localStorage.setItem("latestValidationReport", JSON.stringify(data));

    router.push("/results");
  }

  async function submitBatch() {
    if (batchImages.length === 0 || !spreadsheet) {
      alert("Please upload label images and a spreadsheet.");
      return;
    }

    const formData = new FormData();

    batchImages.forEach((image) => {
      formData.append("images", image);
    });

    formData.append("spreadsheet", spreadsheet);

    const response = await fetch("http://localhost:8000/batch-label-check", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    localStorage.setItem("latestValidationReport", JSON.stringify(data));

    router.push("/results");
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);

    try {
      if (mode === "single") {
        await submitSingle(event.currentTarget);
      } else {
        await submitBatch();
      }
    } catch {
      alert("Upload failed. Make sure the backend is running on port 8000.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="mb-6 text-3xl font-bold">Upload Alcohol Label</h1>

      <div className="mb-6 flex gap-3">
        <button
          type="button"
          onClick={() => setMode("single")}
          className={`rounded border px-4 py-2 ${
            mode === "single" ? "bg-black text-white" : "bg-white text-black"
          }`}
        >
          Single Label
        </button>

        <button
          type="button"
          onClick={() => setMode("batch")}
          className={`rounded border px-4 py-2 ${
            mode === "batch" ? "bg-black text-white" : "bg-white text-black"
          }`}
        >
          Batch Upload
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {mode === "single" && (
          <>
            <div>
              <label className="mb-1 block font-medium">Label Image</label>
              <input
                type="file"
                accept=".jpg,.jpeg,.png"
                onChange={(event) =>
                  setSingleImage(event.target.files?.[0] ?? null)
                }
                required
              />
            </div>

            <Input name="brandName" label="Brand Name" />
            <Input name="className" label="Class / Type Designation" />
            <Input name="alcoholContent" label="Alcohol Content" />
            <Input name="netContents" label="Net Contents" />
            <Input name="address" label="Name and Address of Bottler / Producer" />
            <Input
              name="importOrigin"
              label="Country of Origin for Imports"
              required={false}
            />

            <div>
              <label className="mb-1 block font-medium">
                Government Health Warning Statement
              </label>
              <textarea
                name="healthWarning"
                className="min-h-28 w-full rounded border p-2"
                placeholder="GOVERNMENT WARNING..."
                required
              />
            </div>
          </>
        )}

        {mode === "batch" && (
          <>
            <div>
              <label className="mb-1 block font-medium">Label Images</label>
              <input
                type="file"
                multiple
                accept=".jpg,.jpeg,.png"
                onChange={(event) =>
                  setBatchImages(Array.from(event.target.files ?? []))
                }
                required
              />
            </div>

            <div>
              <label className="mb-1 block font-medium">Spreadsheet</label>
              <input
                type="file"
                accept=".csv,.xlsx"
                onChange={(event) =>
                  setSpreadsheet(event.target.files?.[0] ?? null)
                }
                required
              />
            </div>
          </>
        )}

        <button
          type="submit"
          disabled={loading}
          className="rounded bg-black px-5 py-2 text-white disabled:opacity-50"
        >
          {loading ? "Processing..." : "Run Label Check"}
        </button>
      </form>
    </main>
  );
}

function Input({
  name,
  label,
  required = true,
}: {
  name: string;
  label: string;
  required?: boolean;
}) {
  return (
    <div>
      <label className="mb-1 block font-medium">{label}</label>
      <input
        name={name}
        className="w-full rounded border p-2"
        required={required}
      />
    </div>
  );
}