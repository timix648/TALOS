import { NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET() {
  try {
    const response = await fetch(`${API_URL}/stats`, {
      headers: {
        'Content-Type': 'application/json',
      },
     
      next: { revalidate: 30 }
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch stats');
    }
    
    const stats = await response.json();
    return NextResponse.json(stats);
  } catch (error) {
    
    return NextResponse.json({
      avg_boot_time_ms: 0,
      fix_rate_percent: 0,
      total_heals: 0,
      successful_heals: 0,
      retry_limit: 3,
      status: 'offline'
    });
  }
}
