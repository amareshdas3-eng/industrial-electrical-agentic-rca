export const dynamic = 'force-static';

import { NextResponse } from 'next/server';

interface Alert {
  status: string;
  labels: {
    alertname: string;
    severity: string;
    service: string;
    [key: string]: string;
  };
  annotations: {
    summary: string;
    description: string;
  };
  receivedAt: string;
}

interface AlertData {
  status: string;
  labels: {
    alertname: string;
    severity: string;
    service: string;
    [key: string]: string;
  };
  annotations: {
    summary: string;
    description: string;
  };
}

let alerts: Alert[] = [];

export async function POST(request: Request) {
  return NextResponse.json({ success: true });
}

export async function GET() {
  return NextResponse.json(alerts);
}
