import { NextResponse } from "next/server";
import { PROFESSIONS } from "@/content/landing";
import { getSupabaseClient } from "@/lib/supabase";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function invalid(fields: Record<string, string[]>) {
  return NextResponse.json(
    {
      status: "error",
      code: "VALIDATION_ERROR",
      message: "Please check the highlighted fields.",
      fields,
    },
    { status: 400 },
  );
}

export async function POST(request: Request) {
  let body: Record<string, unknown>;
  try {
    body = (await request.json()) as Record<string, unknown>;
  } catch {
    return NextResponse.json(
      { status: "error", code: "INVALID_JSON", message: "Invalid request." },
      { status: 400 },
    );
  }

  const name = typeof body.name === "string" ? body.name.trim() : "";
  const email =
    typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
  const profession =
    typeof body.profession === "string" ? body.profession : "";

  const fields: Record<string, string[]> = {};
  if (name.length < 2 || name.length > 80) fields.name = ["Enter your name."];
  if (!EMAIL_RE.test(email) || email.length > 254)
    fields.email = ["Enter a valid email address."];
  if (!(PROFESSIONS as readonly string[]).includes(profession))
    fields.profession = ["Choose what you do."];
  if (Object.keys(fields).length) return invalid(fields);

  const source =
    typeof body.source === "string" && body.source.trim()
      ? body.source.trim().slice(0, 40)
      : "unknown";
  const cryptoInterest = body.crypto_interest === true;

  try {
    const supabase = getSupabaseClient();
    const { error } = await supabase.from("waitlist").insert({
      name,
      email,
      profession,
      source,
      crypto_interest: cryptoInterest,
    });

    if (error) {
      // Postgres unique constraint violation (waitlist_email_key)
      if (error.code === "23505") {
        return NextResponse.json(
          {
            status: "error",
            code: "DUPLICATE",
            message: "Already on the list.",
          },
          { status: 409 },
        );
      }
      console.error("waitlist.supabase_error", {
        code: error.code,
        message: error.message,
      });
      return NextResponse.json(
        {
          status: "error",
          code: "SERVER_ERROR",
          message: "Something went wrong.",
        },
        { status: 500 },
      );
    }

    return NextResponse.json(
      {
        status: "success",
        data: { email },
        message: "Joined the waitlist.",
      },
      { status: 201 },
    );
  } catch (err) {
    console.error("waitlist.write_failed", err);
    return NextResponse.json(
      {
        status: "error",
        code: "SERVER_ERROR",
        message: "Something went wrong.",
      },
      { status: 500 },
    );
  }
}
