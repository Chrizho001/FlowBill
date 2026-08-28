import { promises as fs } from "fs";
import path from "path";
import { NextResponse } from "next/server";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const DATA_DIR = path.join(process.cwd(), "data");
const DATA_FILE = path.join(DATA_DIR, "waitlist.json");

type WaitlistEntry = { email: string; joinedAt: string };

async function readWaitlist(): Promise<WaitlistEntry[]> {
  try {
    const raw = await fs.readFile(DATA_FILE, "utf-8");
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as WaitlistEntry[]) : [];
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") return [];
    throw err;
  }
}

async function writeWaitlist(entries: WaitlistEntry[]): Promise<void> {
  await fs.mkdir(DATA_DIR, { recursive: true });
  await fs.writeFile(DATA_FILE, JSON.stringify(entries, null, 2), "utf-8");
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { status: "error", message: "Invalid JSON body." },
      { status: 400 },
    );
  }

  const email =
    typeof body === "object" && body !== null && "email" in body
      ? String((body as { email: unknown }).email).trim().toLowerCase()
      : "";

  if (!EMAIL_RE.test(email) || email.length > 254) {
    return NextResponse.json(
      { status: "error", message: "Please enter a valid email address." },
      { status: 400 },
    );
  }

  try {
    const entries = await readWaitlist();
    if (entries.some((e) => e.email === email)) {
      return NextResponse.json(
        { status: "error", message: "This email is already on the waitlist." },
        { status: 409 },
      );
    }

    entries.push({ email, joinedAt: new Date().toISOString() });
    await writeWaitlist(entries);

    return NextResponse.json(
      { status: "success", data: { position: entries.length } },
      { status: 201 },
    );
  } catch {
    return NextResponse.json(
      { status: "error", message: "Something went wrong. Please try again." },
      { status: 500 },
    );
  }
}
