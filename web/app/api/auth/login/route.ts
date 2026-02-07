import { NextRequest, NextResponse } from "next/server";


const GITHUB_CLIENT_ID = process.env.GITHUB_CLIENT_ID;

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

export async function GET(request: NextRequest) {
  if (!GITHUB_CLIENT_ID) {
    return NextResponse.json(
      { error: "GitHub Client ID not configured" },
      { status: 500 }
    );
  }

  const callbackUrl = `${APP_URL}/api/auth/callback/github`;
  
  const scopes = "read:user user:email";
  
  const githubAuthUrl = new URL("https://github.com/login/oauth/authorize");
  githubAuthUrl.searchParams.set("client_id", GITHUB_CLIENT_ID);
  githubAuthUrl.searchParams.set("redirect_uri", callbackUrl);
  githubAuthUrl.searchParams.set("scope", scopes);
  githubAuthUrl.searchParams.set("state", crypto.randomUUID()); 

  return NextResponse.redirect(githubAuthUrl.toString());
}