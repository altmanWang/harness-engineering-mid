import { NextRequest, NextResponse } from "next/server"
import { listSessions, saveSession, deleteSession } from "@/lib/chat/session-store"
import type { ChatSession } from "@/types/chat"

export async function GET() {
  const sessions = await listSessions()
  return NextResponse.json({ sessions })
}

export async function POST(request: NextRequest) {
  try {
    const { engine, model } = await request.json()
    const session: ChatSession = {
      id: `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      title: "", engine: engine || "claude-code", model: model || "claude-sonnet-4-6",
      messages: [], createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
    }
    await saveSession(session)
    return NextResponse.json({ session })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { id } = await request.json()
    if (!id) return NextResponse.json({ error: "Missing id" }, { status: 400 })
    await deleteSession(id)
    return NextResponse.json({ deleted: true })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
