import { NextRequest, NextResponse } from "next/server";
import { listJobs, createJob, JobType, JobStatus } from "@/lib/db";

export async function GET(req: NextRequest) {
  try {
    const status = req.nextUrl.searchParams.get("status") as JobStatus | null;
    const client_id = req.nextUrl.searchParams.get("client_id") ?? undefined;

    const jobs = listJobs({
      status: status ?? undefined,
      client_id,
    });

    return NextResponse.json({ jobs, total: jobs.length });
  } catch (err) {
    console.error("[GET /api/jobs]", err);
    return NextResponse.json({ error: "Failed to fetch jobs" }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json() as {
      client_id?: string;
      title?: string;
      type?: JobType;
      status?: JobStatus;
      date?: string;
      amount_usd?: number;
      notes?: string;
    };

    if (!body.client_id) {
      return NextResponse.json({ error: "client_id is required" }, { status: 400 });
    }
    if (!body.title || body.title.trim() === "") {
      return NextResponse.json({ error: "title is required" }, { status: 400 });
    }

    const job = createJob({
      client_id: body.client_id,
      title: body.title.trim(),
      type: body.type ?? "excavation",
      status: body.status ?? "pending",
      date: body.date ?? null,
      amount_usd: Number(body.amount_usd ?? 0),
      notes: body.notes?.trim() ?? null,
    });

    return NextResponse.json({ job }, { status: 201 });
  } catch (err) {
    console.error("[POST /api/jobs]", err);
    return NextResponse.json({ error: "Failed to create job" }, { status: 500 });
  }
}
