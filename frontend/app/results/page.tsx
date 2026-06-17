"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import * as XLSX from "xlsx";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

type ValidationStatus = "PASS" | "WARNING" | "FAIL" | "SKIPPED" | "ERROR";

type Validation = {
  field: string;
  expected: string;
  found: string;
  status: ValidationStatus;
  reason?: string;
};

type ReportItem = {
  imageFilename?: string;
  labelName?: string;
  status?: string;
  matched?: boolean;
  error?: string;
  errorType?: string;
  validations?: Validation[];
  ocrText?: string;
};

type ExportRow = {
  imageFilename: string;
  labelName: string;
  overallStatus: string;
  field: string;
  expected: string;
  found: string;
  status: string;
  reason: string;
  errorType: string;
  error: string;
};

export default function ResultsPage() {
  const [reportItems, setReportItems] = useState<ReportItem[]>([]);
  const [rawReport, setRawReport] = useState<any>(null);

  useEffect(() => {
    const stored = localStorage.getItem("latestValidationReport");

    if (!stored) {
      return;
    }

    const parsed = JSON.parse(stored);
    setRawReport(parsed);

    if (parsed.mode === "batch") {
      setReportItems(parsed.report ?? []);
    } else {
      setReportItems([
        {
          imageFilename: parsed.imageFilename,
          labelName: parsed.imageFilename,
          status: parsed.status,
          matched: true,
          validations: parsed.validations ?? [],
          ocrText: parsed.ocrText ?? "",
          error: parsed.error,
          errorType: parsed.errorType,
        },
      ]);
    }
  }, []);

  function buildExportRows(): ExportRow[] {
    const rows: ExportRow[] = [];

    reportItems.forEach((item) => {
      if (!item.validations || item.validations.length === 0) {
        rows.push({
          imageFilename: item.imageFilename ?? "",
          labelName: item.labelName ?? "",
          overallStatus: item.status ?? "",
          field: "",
          expected: "",
          found: "",
          status: item.status ?? "",
          reason: "",
          errorType: item.errorType ?? "",
          error: item.error ?? "",
        });

        return;
      }

      item.validations.forEach((validation) => {
        rows.push({
          imageFilename: item.imageFilename ?? "",
          labelName: item.labelName ?? "",
          overallStatus: item.status ?? "",
          field: validation.field,
          expected: validation.expected,
          found: validation.found,
          status: validation.status,
          reason: validation.reason ?? "",
          errorType: item.errorType ?? "",
          error: item.error ?? "",
        });
      });
    });

    return rows;
  }

  function exportCsv() {
    const rows = buildExportRows();

    const headers = [
      "imageFilename",
      "labelName",
      "overallStatus",
      "field",
      "expected",
      "found",
      "status",
      "reason",
      "errorType",
      "error",
    ];

    const csv = [
      headers.join(","),
      ...rows.map((row) =>
        headers
          .map((header) => {
            const value = String(row[header as keyof ExportRow] ?? "");
            return `"${value.replaceAll('"', '""')}"`;
          })
          .join(",")
      ),
    ].join("\n");

    downloadFile("validation-report.csv", csv, "text/csv");
  }

  function exportExcel() {
    const rows = buildExportRows();

    const worksheet = XLSX.utils.json_to_sheet(rows);
    const workbook = XLSX.utils.book_new();

    XLSX.utils.book_append_sheet(workbook, worksheet, "Validation Report");
    XLSX.writeFile(workbook, "validation-report.xlsx");
  }

  function exportPdf() {
    const rows = buildExportRows();

    const doc = new jsPDF();

    doc.text("Alcohol Label Validation Report", 14, 15);

    autoTable(doc, {
      startY: 22,
      head: [
        [
          "Image",
          "Label",
          "Overall",
          "Field",
          "Expected",
          "Found",
          "Status",
          "Reason",
        ],
      ],
      body: rows.map((row) => [
        row.imageFilename,
        row.labelName,
        row.overallStatus,
        row.field,
        row.expected,
        row.found,
        row.status,
        row.reason || row.error,
      ]),
      styles: {
        fontSize: 7,
        cellPadding: 2,
      },
      headStyles: {
        fontStyle: "bold",
      },
    });

    doc.save("validation-report.pdf");
  }

  function downloadFile(filename: string, content: string, mimeType: string) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();

    URL.revokeObjectURL(url);
  }

  if (!rawReport) {
    return (
      <main className="mx-auto max-w-5xl p-8">
        <h1 className="mb-4 text-3xl font-bold">Validation Report</h1>

        <p className="mb-6 text-gray-600">
          No validation report found. Run an upload first.
        </p>

        <Link href="/upload" className="rounded bg-black px-4 py-2 text-white">
          Go to Upload
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl p-8">
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Validation Report</h1>
          <p className="mt-1 text-gray-600">
            Mode: {rawReport.mode} | Status: {rawReport.status}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={exportCsv}
            className="rounded border px-4 py-2"
          >
            Export CSV
          </button>

          <button
            type="button"
            onClick={exportExcel}
            className="rounded border px-4 py-2"
          >
            Export Excel
          </button>

          <button
            type="button"
            onClick={exportPdf}
            className="rounded border px-4 py-2"
          >
            Export PDF
          </button>

          <Link href="/upload" className="rounded bg-black px-4 py-2 text-white">
            Run Another Check
          </Link>
        </div>
      </div>

      <div className="space-y-8">
        {reportItems.map((item, index) => (
          <section key={index} className="rounded border p-4">
            <div className="mb-4">
              <h2 className="text-xl font-semibold">
                {item.imageFilename ?? `Label ${index + 1}`}
              </h2>

              <p className="text-sm text-gray-600">
                Label Name: {item.labelName ?? "N/A"} | Overall Status:{" "}
                {item.status ?? "N/A"}
              </p>

              {item.error && (
                <p className="mt-2 rounded bg-red-100 p-2 text-sm text-red-800">
                  {item.errorType ? `${item.errorType}: ` : ""}
                  {item.error}
                </p>
              )}
            </div>

            <div className="overflow-hidden rounded border">
              <table className="w-full border-collapse text-left">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="border-b p-3">Field</th>
                    <th className="border-b p-3">Expected</th>
                    <th className="border-b p-3">Found</th>
                    <th className="border-b p-3">Status</th>
                    <th className="border-b p-3">Reason</th>
                  </tr>
                </thead>

                <tbody>
                  {(item.validations ?? []).length > 0 ? (
                    item.validations?.map((validation, validationIndex) => (
                      <tr key={validationIndex}>
                        <td className="border-b p-3 font-medium">
                          {validation.field}
                        </td>
                        <td className="border-b p-3">{validation.expected}</td>
                        <td className="border-b p-3">{validation.found}</td>
                        <td className="border-b p-3">
                          <StatusBadge status={validation.status} />
                        </td>
                        <td className="border-b p-3 text-sm text-gray-600">
                          {validation.reason ?? ""}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="p-3 text-sm text-gray-600">
                        No validation rows available.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {item.ocrText && (
              <details className="mt-4">
                <summary className="cursor-pointer font-medium">
                  View OCR Text
                </summary>

                <pre className="mt-2 max-h-80 overflow-auto rounded bg-gray-100 p-3 text-sm">
                  {item.ocrText}
                </pre>
              </details>
            )}
          </section>
        ))}
      </div>
    </main>
  );
}

function StatusBadge({ status }: { status: ValidationStatus }) {
  const className =
    status === "PASS"
      ? "bg-green-100 text-green-800"
      : status === "WARNING"
        ? "bg-yellow-100 text-yellow-800"
        : status === "SKIPPED"
          ? "bg-gray-100 text-gray-800"
          : "bg-red-100 text-red-800";

  return (
    <span className={`rounded px-2 py-1 text-sm font-semibold ${className}`}>
      {status}
    </span>
  );
}