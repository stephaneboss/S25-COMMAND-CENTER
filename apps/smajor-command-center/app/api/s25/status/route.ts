import { NextResponse } from "next/server";
import type { CommandCenterSnapshot } from "@/lib/s25-api";

const COCKPIT_URL = process.env.S25_COCKPIT_URL || "https://s25.smajor.org";
const CACHE_TTL_MS = 30_000; // 30 seconds

// Simple in-memory cache (per server process)
let cachedData: CommandCenterSnapshot | null = null;
let cacheTimestamp = 0;

export async function GET() {
  const now = Date.now();

  // Return cached response if still fresh
  if (cachedData && now - cacheTimestamp < CACHE_TTL_MS) {
    return NextResponse.json({
      ...cachedData,
      cached: true,
      cache_age_ms: now - cacheTimestamp,
    });
  }

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    const res = await fetch(`${COCKPIT_URL}/api/status`, {
      signal: controller.signal,
      cache: "no-store",
    });
    clearTimeout(timeout);

    if (!res.ok) {
      throw new Error(`Cockpit returned HTTP ${res.status}`);
    }

    const data = await res.json() as CommandCenterSnapshot;
    cachedData = data;
    cacheTimestamp = now;

    return NextResponse.json({
      ...data,
      cached: false,
      cache_age_ms: 0,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";

    // Return stale cache if available
    if (cachedData) {
      return NextResponse.json({
        ...cachedData,
        cached: true,
        stale: true,
        cache_age_ms: now - cacheTimestamp,
        error: `Cockpit unreachable: ${message}`,
      });
    }

    // No cache at all — return degraded status
    return NextResponse.json(
      {
        timestamp: new Date().toISOString(),
        error: `S25 Cockpit unreachable: ${message}`,
        ha_connected: false,
        pipeline_active: false,
        merlin_status: "offline",
        cockpit_version: "unknown",
        total_signals_today: 0,
        agents: [
          { name: "TRINITY", status: "unknown", last_seen: null, model: "GPT-4o" },
          { name: "ARKON",   status: "unknown", last_seen: null, model: "Claude Sonnet 4.6" },
          { name: "MERLIN",  status: "unknown", last_seen: null, model: "Gemini 1.5 Pro" },
          { name: "COMET",   status: "unknown", last_seen: null, model: "Perplexity" },
          { name: "KIMI",    status: "unknown", last_seen: null, model: "Kimi Web3" },
        ],
        cached: false,
      },
      { status: 503 }
    );
  }
}
