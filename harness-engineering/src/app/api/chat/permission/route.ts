import { NextRequest, NextResponse } from "next/server"
import { resolvePermission } from "@/lib/chat/permission-queue"

export async function POST(request: NextRequest) {
  try {
    const { requestId, optionId } = await request.json()
    if (!requestId || !optionId) return NextResponse.json({ error: "Missing requestId or optionId" }, { status: 400 })
    const resolved = resolvePermission(requestId, optionId)
    if (!resolved) return NextResponse.json({ error: "Permission request not found" }, { status: 404 })
    return NextResponse.json({ resolved: true })
  } catch (error: any) {
    return NextResponse.json({ error: error.message || "Failed" }, { status: 500 })
  }
}
