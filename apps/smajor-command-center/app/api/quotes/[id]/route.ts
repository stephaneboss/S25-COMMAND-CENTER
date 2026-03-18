import { NextRequest, NextResponse } from "next/server";
import { getQuote, updateQuote, softDeleteQuote, QuoteStatus, QuoteItem } from "@/lib/db";

interface Params {
  params: Promise<{ id: string }>;
}

export async function GET(_req: NextRequest, { params }: Params) {
  try {
    const { id } = await params;
    const quote = getQuote(id);
    if (!quote) {
      return NextResponse.json({ error: "Quote not found" }, { status: 404 });
    }
    return NextResponse.json({ quote });
  } catch (err) {
    console.error("[GET /api/quotes/[id]]", err);
    return NextResponse.json({ error: "Failed to fetch quote" }, { status: 500 });
  }
}

export async function PUT(req: NextRequest, { params }: Params) {
  try {
    const { id } = await params;
    const body = await req.json() as {
      client_id?: string;
      job_id?: string;
      amount_usd?: number;
      status?: QuoteStatus;
      valid_until?: string;
      items?: QuoteItem[];
    };

    const updateData: Parameters<typeof updateQuote>[1] = {};
    if (body.client_id !== undefined) updateData.client_id = body.client_id;
    if (body.job_id !== undefined) updateData.job_id = body.job_id ?? null;
    if (body.amount_usd !== undefined) updateData.amount_usd = Number(body.amount_usd);
    if (body.status !== undefined) updateData.status = body.status;
    if (body.valid_until !== undefined) updateData.valid_until = body.valid_until ?? null;
    if (body.items !== undefined) updateData.items = body.items;

    const updated = updateQuote(id, updateData);
    if (!updated) {
      return NextResponse.json({ error: "Quote not found" }, { status: 404 });
    }
    return NextResponse.json({ quote: updated });
  } catch (err) {
    console.error("[PUT /api/quotes/[id]]", err);
    return NextResponse.json({ error: "Failed to update quote" }, { status: 500 });
  }
}

export async function DELETE(_req: NextRequest, { params }: Params) {
  try {
    const { id } = await params;
    const deleted = softDeleteQuote(id);
    if (!deleted) {
      return NextResponse.json({ error: "Quote not found" }, { status: 404 });
    }
    return NextResponse.json({ success: true, id });
  } catch (err) {
    console.error("[DELETE /api/quotes/[id]]", err);
    return NextResponse.json({ error: "Failed to delete quote" }, { status: 500 });
  }
}
