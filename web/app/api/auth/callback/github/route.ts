import { NextRequest, NextResponse } from "next/server";

/**
 * GitHub OAuth Callback Handler
 * ================================
 * Handles both:
 * 1. Simple OAuth login ("Sign in with GitHub")
 * 2. GitHub App installation callbacks
 */

const GITHUB_CLIENT_ID = process.env.GITHUB_CLIENT_ID;
const GITHUB_CLIENT_SECRET = process.env.GITHUB_CLIENT_SECRET;
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

interface GitHubTokenResponse {
  access_token: string;
  token_type: string;
  scope: string;
  error?: string;
  error_description?: string;
}

interface GitHubUser {
  id: number;
  login: string;
  avatar_url: string;
  name: string;
}

interface GitHubInstallation {
  id: number;
  account: {
    login: string;
    type: string;
  };
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  
  const code = searchParams.get("code");
  const installationId = searchParams.get("installation_id");
  const setupAction = searchParams.get("setup_action");
  
  console.log("🔐 GitHub Callback:", { hasCode: !!code, installationId, setupAction });

  // No code = something went wrong
  if (!code) {
    // If we have installation_id but no code, user installed app without OAuth enabled
    if (installationId) {
      console.log(`⚠️ App installed without OAuth. Installation: ${installationId}`);
      return NextResponse.redirect(
        new URL(`/?message=installed&installation=${installationId}`, APP_URL)
      );
    }
    
    return NextResponse.redirect(
      new URL("/?error=no_code", APP_URL)
    );
  }

  // Validate config
  if (!GITHUB_CLIENT_ID || !GITHUB_CLIENT_SECRET) {
    console.error("❌ Missing GitHub OAuth credentials");
    return NextResponse.redirect(
      new URL("/?error=config", APP_URL)
    );
  }

  try {
    // Step 1: Exchange code for access token
    console.log("🔄 Exchanging code for token...");
    
    const tokenResponse = await fetch("https://github.com/login/oauth/access_token", {
      method: "POST",
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        client_id: GITHUB_CLIENT_ID,
        client_secret: GITHUB_CLIENT_SECRET,
        code,
      }),
    });

    const tokenData: GitHubTokenResponse = await tokenResponse.json();

    if (tokenData.error) {
      console.error("❌ Token error:", tokenData.error_description);
      return NextResponse.redirect(
        new URL(`/?error=${tokenData.error}`, APP_URL)
      );
    }

    console.log("✅ Got access token");

    // Step 2: Get user info
    const userResponse = await fetch("https://api.github.com/user", {
      headers: {
        "Authorization": `Bearer ${tokenData.access_token}`,
        "Accept": "application/vnd.github+json",
      },
    });

    if (!userResponse.ok) {
      throw new Error("Failed to fetch user info");
    }

    const user: GitHubUser = await userResponse.json();
    console.log(`✅ User: ${user.login}`);

    // Step 3: Get user's installations of our GitHub App
    let installations: GitHubInstallation[] = [];
    let primaryInstallationId: number | null = installationId ? parseInt(installationId) : null;

    try {
      const installResponse = await fetch("https://api.github.com/user/installations", {
        headers: {
          "Authorization": `Bearer ${tokenData.access_token}`,
          "Accept": "application/vnd.github+json",
        },
      });

      if (installResponse.ok) {
        const data = await installResponse.json();
        installations = data.installations || [];
        console.log(`📦 Found ${installations.length} installation(s)`);

        // Use first installation if we don't have one
        if (!primaryInstallationId && installations.length > 0) {
          primaryInstallationId = installations[0].id;
        }
      }
    } catch (err) {
      console.log("⚠️ Could not fetch installations (user may not have installed the app yet)");
    }

    // Step 4: Sync installations with backend (non-blocking - fire and forget)
    // This runs in the background - we don't wait for it
    if (installations.length > 0) {
      Promise.allSettled(
        installations.map(inst =>
          fetch(`${API_BASE_URL}/installations`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              github_installation_id: inst.id,
              account_login: inst.account.login,
              account_type: inst.account.type,
            }),
          })
        )
      ).then(results => {
        results.forEach((result, i) => {
          if (result.status === 'rejected') {
            console.error(`❌ Failed to sync installation ${installations[i].id}:`, result.reason);
          }
        });
      });
    }

    // Step 5: Create session and redirect
    const session = {
      user: {
        id: user.id,
        login: user.login,
        avatar_url: user.avatar_url,
        name: user.name,
      },
      access_token: tokenData.access_token,
      installation_id: primaryInstallationId,
      installations: installations.map(i => ({ id: i.id, account: i.account.login })),
    };

    // Redirect to appropriate page
    let redirectUrl = "/dashboard";
    
    // If user has no installations, prompt them to install the app
    if (installations.length === 0) {
      redirectUrl = "/?need_install=true";
    }

    const response = NextResponse.redirect(new URL(redirectUrl, APP_URL));

    // Set session cookie
    response.cookies.set("talos_session", JSON.stringify(session), {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 7, // 7 days
      path: "/",
    });

    console.log(`✅ Session created, redirecting to ${redirectUrl}`);
    return response;

  } catch (error) {
    console.error("❌ OAuth error:", error);
    return NextResponse.redirect(
      new URL("/?error=auth_failed", APP_URL)
    );
  }
}
