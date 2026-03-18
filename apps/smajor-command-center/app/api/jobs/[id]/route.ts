import { NextRequest, NextResponse } from "next/server";
import { getJob, updateJob, softDeleteJob, JobType, JobStatus } from "@/lib/db";

interface Params {
  params: Promise<{ id: string }>;
}

export async function GET(_req: NextRequest, { params }: Params) {
  try {
    const { id } = await params;
    const job = getJob(id);
    if (!job) {
      return NextResponse.json({ error: "Job not found" }, { status: 404 });
    }
    return NextResponse.json({ job });
  } catch (err) {
    console.error("[GET /api/jobs/[id]]", err);
    return NextResponse.json({ error: "Failed to fetch job" }, { status: 500 });
  }
}

export async function PUT(req: NextRequest, { params }: Params) {
  try {
    const { id } = await params;
    const body = await req.json() as {
      client_id?: string;
      title?: string;
      type?: JobType;
      status?: JobStatus;
      date?: string;
      amount_usd?: number;
      notes?: string;
    };

    const updated = updateJob(id, {
      ...(body.client_id !== undefined && { client_id: body.client_id }),
      ...(body.title !== undefined && { title: body.title.trim() }),
      ...(body.type !== undefined && { type: body.type }),
      ...(body.status !== undefined && { status: body.status }),
      ...(body.date !== undefined && { date: body.date ?? null }),
      ...(body.amount_usd !== undefined && { amount_usd: Number(body.amount_usd) }),
      ...(body.notes !== undefined && { notes: body.notes?.trim() ?? null }),
    });

    if (!updated) {
      return NextResponse.json({ error: "Job not found" }, { status: 404 });
    }
    return NextResponse.json({ job: updated });
  } catch (err) {
    console.error("[PUT /api/jobs/[id]]", err);
    return NextResponse.json({ error: "Failed to update job" }, { status: 500 });
  }
}

export async function DELETE(_req: NextRequest, { params }: Params) {
  try {
    const { id } = await params;
    const deleted = softDeleteJob(id);
    if (!deleted) {
      return NextResponse.json({ error: "Job not found" }, { status: 404 });
    }
    return NextResponse.json({ success: true, id });
  } catch (err) {
    console.error("[DELETE /api/jobs/[id]]", err);
    return NextResponse.json({ error: "Failed to delete job" }, { status: 500 });
  }
}
