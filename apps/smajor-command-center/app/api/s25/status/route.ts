import { NextResponse } from "next/server";
import type { CommandCenterSnapshot } from "@/lib/s25-api";


const COCKPIT_URL = process.env.S25_COCKPIT_URL || "http://provider.team-michel.com:31554";
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

