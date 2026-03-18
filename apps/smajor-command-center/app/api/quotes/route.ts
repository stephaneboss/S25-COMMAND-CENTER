import { NextRequest, NextResponse } from "next/server";
import { listQuotes, createQuote, QuoteStatus, QuoteItem } from "@/lib/db";

export async function GET(req: NextRequest) {
  try {
    const status = req.nextUrl.searchParams.get("status") as QuoteStatus | null;
    const client_id = req.nextUrl.searchParams.get("client_id") ?? undefined;

    const quotes = listQuotes({
      status: status ?? undefined,
      client_id,
    });

    return NextResponse.json({ quotes, total: quotes.length });
  } catch (err) {
    console.error("[GET /api/quotes]", err);
    return NextResponse.json({ error: "Failed to fetch quotes" }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json() as {
      client_id?: string;
      job_id?: string;
      amount_usd?: number;
      status?: QuoteStatus;
      valid_until?: string;
      items?: QuoteItem[];
    };

    if (!body.client_id) {
      return NextResponse.json({ error: "client_id is required" }, { status: 400 });
    }

    // Auto-compute amount from items if not specified
    const items: QuoteItem[] = body.items ?? [];
    const computedAmount = items.reduce((sum, item) => sum + (item.total ?? item.quantity * item.unit_price), 0);
    const amount_usd = body.amount_usd !== undefined ? Number(body.amount_usd) : computedAmount;

    const quote = createQuote({
      client_id: body.client_id,
      job_id: body.job_id ?? null,
      amount_usd,
      status: body.status ?? "draft",
      valid_until: body.valid_until ?? null,
      items,
    });

    return NextResponse.json({ quote }, { status: 201 });
  } catch (err) {
    console.error("[POST /api/quotes]", err);
    return NextResponse.json({ error: "Failed to create quote" }, { status: 500 });
  }
}
