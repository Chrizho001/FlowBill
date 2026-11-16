/**
 * TEMPORARY waitlist handler (design.md §5, open decision 1).
 * Stores entries in frontend/data/waitlist.json locally, or /tmp on Vercel (ephemeral).
 * Replace with the Django `POST /api/v1/waitlist/` endpoint (throttled) before deploying.
 */
import { promises as fs } from "fs";
import path from "path";
import { NextResponse } from "next/server";
import { PROFESSIONS } from "@/content/landing";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
// Vercel's filesystem is read-only except /tmp. There, entries are ephemeral (lost on cold starts/redeploys).
const DATA_DIR = process.env.VERCEL ? "/tmp/flowbill-data" : path.join(process.cwd(), "data");
const DATA_FILE = path.join(DATA_DIR, "waitlist.json");

type Entry = {
  name: string;
  email: string;
  profession: string;
  source: string;
  crypto_interest: boolean;
  joinedAt: string;
};

async function read(): Promise<Entry[]> {
  try {
    const parsed: unknown = JSON.parse(await fs.readFile(DATA_FILE, "utf-8"));
    return Array.isArray(parsed) ? (parsed as Entry[]) : [];
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") return [];
    throw err;
  }
}

function invalid(fields: Record<string, string[]>) {
  return NextResponse.json(
    { status: "error", code: "VALIDATION_ERROR", message: "Please check the highlighted fields.", fields },
    { status: 400 },
  );
}

export async function POST(request: Request) {
  let body: Record<string, unknown>;
  try {
    body = (await request.json()) as Record<string, unknown>;
  } catch {
    return NextResponse.json({ status: "error", code: "INVALID_JSON", message: "Invalid request." }, { status: 400 });
  }

  const name = typeof body.name === "string" ? body.name.trim() : "";
  const email = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
  const profession = typeof body.profession === "string" ? body.profession : "";

  const fields: Record<string, string[]> = {};
  if (name.length < 2 || name.length > 80) fields.name = ["Enter your name."];
  if (!EMAIL_RE.test(email) || email.length > 254) fields.email = ["Enter a valid email address."];
  if (!(PROFESSIONS as readonly string[]).includes(profession)) fields.profession = ["Choose what you do."];
  if (Object.keys(fields).length) return invalid(fields);

  try {
    const entries = await read();
    if (entries.some((e) => e.email === email)) {
      return NextResponse.json({ status: "error", code: "DUPLICATE", message: "Already on the list." }, { status: 409 });
    }
    entries.push({
      name,
      email,
      profession,
      source: typeof body.source === "string" ? body.source.slice(0, 40) : "unknown",
      crypto_interest: body.crypto_interest === true,
      joinedAt: new Date().toISOString(),
    });
    await fs.mkdir(DATA_DIR, { recursive: true });
    await fs.writeFile(DATA_FILE, JSON.stringify(entries, null, 2), "utf-8");
    return NextResponse.json({ status: "success", data: { email }, message: "Joined the waitlist." }, { status: 201 });
  } catch (err) {
    console.error("waitlist.write_failed", err);
    return NextResponse.json({ status: "error", code: "SERVER_ERROR", message: "Something went wrong." }, { status: 500 });
  }
}
