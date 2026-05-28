import { NextResponse } from "next/server"
import { detectEngines } from "@/lib/engines/engine-factory"

export const dynamic = "force-dynamic"

export async function GET() {
  const engines = await detectEngines()
  return NextResponse.json({ engines })
}
