import { NextRequest, NextResponse } from "next/server";
import { listClients, createClient, ClientType } from "@/lib/db";

export async function GET(req: NextRequest) {
  try {
    const search = req.nextUrl.searchParams.get("search") ?? undefined;
    const clients = listClients(search);
    return NextResponse.json({ clients, total: clients.length });
  } catch (err) {
    console.error("[GET /api/clients]", err);
    return NextResponse.json({ error: "Failed to fetch clients" }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json() as {
      name?: string;
      phone?: string;
      email?: string;
      address?: string;
      type?: ClientType;
      notes?: string;
    };

    if (!body.name || body.name.trim() === "") {
      return NextResponse.json({ error: "name is required" }, { status: 400 });
    }

    const client = createClient({
      name: body.name.trim(),
      phone: body.phone?.trim() ?? null,
      email: body.email?.trim() ?? null,
      address: body.address?.trim() ?? null,
      type: body.type ?? "residential",
      notes: body.notes?.trim() ?? null,
    });

    return NextResponse.json({ client }, { status: 201 });
  } catch (err) {
    console.error("[POST /api/clients]", err);
    return NextResponse.json({ error: "Failed to create client" }, { status: 500 });
  }
}
