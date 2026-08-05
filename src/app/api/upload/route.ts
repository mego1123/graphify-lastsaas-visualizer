/**
 * Upload API — accepts a .zip file, extracts it, runs graphify frontend analysis.
 *
 * POST /api/upload
 *   Body: multipart/form-data with field "file" = .zip file
 *   Response: { ok: true, sessionId: "abc123", files: [...] }
 *
 * The zip is extracted to /tmp/graphify-uploads/<sessionId>/
 * Analysis results are stored in /tmp/graphify-uploads/<sessionId>/results/
 */

import { NextRequest, NextResponse } from 'next/server'
import { writeFile, mkdir, readFile } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'
import { randomUUID } from 'crypto'
import { execSync } from 'child_process'

const UPLOAD_DIR = '/tmp/graphify-uploads'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File

    if (!file) {
      return NextResponse.json({ error: 'No file uploaded' }, { status: 400 })
    }

    if (!file.name.endsWith('.zip')) {
      return NextResponse.json({ error: 'Only .zip files are accepted' }, { status: 400 })
    }

    // Create session directory
    const sessionId = randomUUID().slice(0, 8)
    const sessionDir = path.join(UPLOAD_DIR, sessionId)
    const extractDir = path.join(sessionDir, 'extracted')
    const resultsDir = path.join(sessionDir, 'results')

    await mkdir(extractDir, { recursive: true })
    await mkdir(resultsDir, { recursive: true })

    // Save the zip file
    const zipPath = path.join(sessionDir, file.name)
    const bytes = await file.arrayBuffer()
    await writeFile(zipPath, Buffer.from(bytes))

    // Extract the zip
    try {
      execSync(`unzip -o "${zipPath}" -d "${extractDir}"`, { timeout: 30000 })
    } catch {
      return NextResponse.json({ error: 'Failed to extract zip file' }, { status: 500 })
    }

    // Find the source directory (might be nested)
    // Look for src/ or frontend/src/ or app/
    let srcPath = extractDir
    const possiblePaths = [
      extractDir,
      path.join(extractDir, file.name.replace('.zip', '')),
    ]

    // Check if there's a package.json in a subdirectory
    for (const p of possiblePaths) {
      if (existsSync(path.join(p, 'package.json')) || existsSync(path.join(p, 'src'))) {
        srcPath = p
        break
      }
    }

    // Look deeper if needed
    try {
      const findResult = execSync(
        `find "${extractDir}" -name "package.json" -not -path "*/node_modules/*" -maxdepth 3 2>/dev/null | head -1`
      ).toString().trim()
      if (findResult) {
        srcPath = path.dirname(findResult)
      }
    } catch {
      // keep default
    }

    // Run the frontend analysis
    const scriptPath = path.join(process.cwd(), '..', 'scripts', 'graphify_frontend.py')
    const pythonScript = existsSync(scriptPath)
      ? scriptPath
      : '/home/z/my-project/scripts/graphify_frontend.py'

    const analyses = [
      { cmd: 'dead-components', file: 'dead-components.json' },
      { cmd: 'route-tree', file: 'route-tree.json' },
      { cmd: 'prop-drilling', file: 'prop-drilling.json' },
      { cmd: 'hook-deps', file: 'hook-deps.json' },
      { cmd: 'context-usage', file: 'context-usage.json' },
      { cmd: 'complexity', file: 'complexity.json' },
      { cmd: 'i18n', file: 'i18n.json' },
      { cmd: 'a11y', file: 'a11y.json' },
      { cmd: 'test-coverage', file: 'test-coverage.json' },
    ]

    const results: Record<string, any> = {}

    for (const { cmd, file } of analyses) {
      try {
        const outputPath = path.join(resultsDir, file)
        execSync(
          `python3 "${pythonScript}" ${cmd} "${srcPath}" --format json --out "${outputPath}"`,
          { timeout: 60000, stdio: 'pipe' }
        )
        if (existsSync(outputPath)) {
          const data = await readFile(outputPath, 'utf-8')
          results[cmd] = JSON.parse(data)
        }
      } catch {
        results[cmd] = null
      }
    }

    // Store session info
    await writeFile(
      path.join(sessionDir, 'info.json'),
      JSON.stringify({
        sessionId,
        filename: file.name,
        uploadedAt: new Date().toISOString(),
        srcPath,
        analysesRun: Object.keys(results).length,
      }, null, 2)
    )

    return NextResponse.json({
      ok: true,
      sessionId,
      filename: file.name,
      extractedTo: srcPath,
      analysesRun: Object.keys(results).length,
      results,
    })
  } catch (error) {
    return NextResponse.json(
      { error: String(error) },
      { status: 500 }
    )
  }
}

export async function GET() {
  // List all uploaded sessions
  try {
    if (!existsSync(UPLOAD_DIR)) {
      return NextResponse.json({ sessions: [] })
    }

    const { readdir } = await import('fs/promises')
    const entries = await readdir(UPLOAD_DIR, { withFileTypes: true })
    const sessions = []

    for (const entry of entries) {
      if (!entry.isDirectory()) continue
      const infoPath = path.join(UPLOAD_DIR, entry.name, 'info.json')
      if (existsSync(infoPath)) {
        const info = JSON.parse(await readFile(infoPath, 'utf-8'))
        sessions.push(info)
      }
    }

    return NextResponse.json({ sessions })
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}
