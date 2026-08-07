/**
 * Next.js middleware for SSO authentication.
 *
 * In production, oauth2-proxy sits in front of the app and authenticates users
 * via OIDC/SAML. It passes the authenticated user as the `X-Forwarded-User`
 * header. This middleware reads that header and sets it as a cookie/env var
 * for the audit logger.
 *
 * If SSO is disabled (GRAPHIFY_SSO_ENABLED=false), all requests are allowed
 * and the user is set to "anonymous".
 */

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const ssoEnabled = process.env.GRAPHIFY_SSO_ENABLED === 'true'

  // Read the SSO user from the oauth2-proxy header
  const ssoUser = request.headers.get('x-forwarded-user') || ''
  const ssoEmail = request.headers.get('x-forwarded-email') || ''
  const ssoGroups = request.headers.get('x-forwarded-groups') || ''

  if (ssoEnabled && !ssoUser) {
    // SSO is enabled but no user header — redirect to oauth2-proxy login
    return NextResponse.redirect(new URL('/oauth2/start', request.url))
  }

  // Set the user info in a response cookie so client-side code can access it
  const response = NextResponse.next()
  if (ssoUser) {
    response.cookies.set('graphify-user', ssoUser, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      path: '/',
    })
    if (ssoEmail) {
      response.cookies.set('graphify-email', ssoEmail, {
        httpOnly: true,
        secure: true,
        sameSite: 'lax',
        path: '/',
      })
    }
  }

  return response
}

export const config = {
  matcher: [
    /*
     * Match all paths except:
     * - _next/static (static files)
     * - _next/image (image optimization)
     * - favicon.ico
     * - public assets (*.json, *.md, *.html)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.json$|.*\\.md$|.*\\.html$).*)',
  ],
}
