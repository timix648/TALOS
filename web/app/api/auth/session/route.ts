import { NextRequest, NextResponse } from "next/server";

/**
 * Get Current Session
 * ====================
 * Returns the current user session from cookies.
 */

export async function GET(request: NextRequest) {
  const sessionCookie = request.cookies.get("talos_session");
  
  if (!sessionCookie?.value) {
    return NextResponse.json({ user: null, logged_in: false }, { status: 200 });
  }

  try {
    const session = JSON.parse(sessionCookie.value);
    return NextResponse.json({
      logged_in: true,
      user: session.user,
      installation_id: session.installation_id,
      installations: session.installations,
      has_installation: !!session.installation_id,
    });
  } catch {
    return NextResponse.json({ user: null, logged_in: false }, { status: 200 });
  }
}

/**
 * Logout
 * =======
 * Clears the session cookie.
 */
export async function DELETE() {
  const response = NextResponse.json({ success: true });
  response.cookies.delete("talos_session");
  return response;
}
