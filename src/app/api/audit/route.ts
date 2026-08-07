/**
 * Audit log API endpoint.
 *
 * POST /api/audit — log an operation
 * GET  /api/audit — query the audit log
 *
 * In production, this runs behind oauth2-proxy which sets the
 * X-Forwarded-User header for identity.
 */

import { NextRequest, NextResponse } from 'next/server'
import { readFile, appendFile, mkdir } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

const AUDIT_LOG = process.env.GRAPHIFY_AUDIT_LOG || path.join(process.cwd(), 'graphify-out', 'audit.log')

type AuditEntry = {
  timestamp: string
  action: string
  user: string
  resource: string
  details: Record<string, unknown>
  source_ip: string
  session_id: string
}

function getUser(request: NextRequest): string {
  const headerUser = request.headers.get('x-forwarded-user')
  if (headerUser) return headerUser

  const cookieUser = request.cookies.get('graphify-user')?.value
  if (cookieUser) return cookieUser

  return 'anonymous'
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const entry: AuditEntry = {
      timestamp: new Date().toISOString(),
      action: body.action || 'unknown',
      user: body.user || getUser(request),
      resource: body.resource || '',
      details: body.details || {},
      source_ip: request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || 'unknown',
      session_id: request.headers.get('x-forwarded-access-token')?.slice(0, 16) || '',
    }

    const dir = path.dirname(AUDIT_LOG)
    if (!existsSync(dir)) {
      await mkdir(dir, { recursive: true })
    }

    await appendFile(AUDIT_LOG, JSON.stringify(entry) + '\n', 'utf-8')

    return NextResponse.json({ ok: true, timestamp: entry.timestamp })
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}

export async function GET(request: NextRequest) {
  try {
    if (!existsSync(AUDIT_LOG)) {
      return NextResponse.json({ entries: [], summary: { total: 0 } })
    }

    const content = await readFile(AUDIT_LOG, 'utf-8')
    const lines = content.trim().split('\n').filter(Boolean)

    const entries: AuditEntry[] = []
    for (const line of lines) {
      try {
        entries.push(JSON.parse(line))
      } catch {
        // skip
      }
    }

    const params = request.nextUrl.searchParams
    const user = params.get('user')
    const action = params.get('action')
    const limit = parseInt(params.get('limit') || '50')

    let filtered = entries
    if (user) filtered = filtered.filter(e => e.user === user)
    if (action) filtered = filtered.filter(e => e.action === action)

    filtered.sort((a, b) => b.timestamp.localeCompare(a.timestamp))

    const byAction: Record<string, number> = {}
    const byUser: Record<string, number> = {}
    for (const e of entries) {
      byAction[e.action] = (byAction[e.action] || 0) + 1
      byUser[e.user] = (byUser[e.user] || 0) + 1
    }

    return NextResponse.json({
      entries: filtered.slice(0, limit),
      summary: {
        total: entries.length,
        by_action: byAction,
        by_user: byUser,
        first_entry: entries[0]?.timestamp,
        last_entry: entries[entries.length - 1]?.timestamp,
      },
    })
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}
