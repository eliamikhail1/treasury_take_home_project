import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6">
      <h1 className="text-4xl font-bold">
        Alcohol Label Validator
      </h1>

      <Link
        href="/upload"
        className="rounded bg-black px-6 py-3 text-white"
      >
        Upload Labels
      </Link>
    </main>
  );
}