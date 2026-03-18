import { NextRequest, NextResponse } from "next/server";
import { getClientWithJobs, updateClient, softDeleteClient, ClientType } from "@/lib/db";

interface Params {
  params: Promise<{ id: string }>;
}

export async function GET(_req: NextRequest, { params }: Params) {
  try {
    const { id } = await params;
    const client = getClientWithJobs(id);
    if (!client) {
      return NextResponse.json({ error: "Client not found" }, { status: 404 });
    }
    return NextResponse.json({ client });
  } catch (err) {
    console.error("[GET /api/clients/[id]]", err);
    return NextResponse.json({ error: "Failed to fetch client" }, { status: 500 });
  }
}

export async function PUT(req: NextRequest, { params }: Params) {
  try {
    const { id } = await params;
    const body = await req.json() as {
      name?: string;
      phone?: string;
      email?: string;
      address?: string;
      type?: ClientType;
      notes?: string;
    };

    const updated = updateClient(id, {
      ...(body.name !== undefined && { name: body.name.trim() }),
      ...(body.phone !== undefined && { phone: body.phone?.trim() ?? null }),
      ...(body.email !== undefined && { email: body.email?.trim() ?? null }),
      ...(body.address !== undefined && { address: body.address?.trim() ?? null }),
      ...(body.type !== undefined && { type: body.type }),
      ...(body.notes !== undefined && { notes: body.notes?.trim() ?? null }),
    });

    if (!updated) {
      return NextResponse.json({ error: "Client not found" }, { status: 404 });
    }
    return NextResponse.json({ client: updated });
  } catch (err) {
    console.error("[PUT /api/clients/[id]]", err);
    return NextResponse.json({ error: "Failed to update client" }, { status: 500 });
  }
}

export async function DELETE(_req: NextRequest, { params }: Params) {
  try {
    const { id } = await params;
    const deleted = softDeleteClient(id);
    if (!deleted) {
      return NextResponse.json({ error: "Client not found" }, { status: 404 });
    }
    return NextResponse.json({ success: true, id });
  } catch (err) {
    console.error("[DELETE /api/clients/[id]]", err);
    return NextResponse.json({ error: "Failed to delete client" }, { status: 500 });
  }
}
