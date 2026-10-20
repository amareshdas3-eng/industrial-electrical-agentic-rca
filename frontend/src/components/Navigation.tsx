'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="fixed left-0 top-0 h-screen w-64 bg-slate-900 text-white shadow-xl border-r border-slate-800">
      <div className="flex flex-col h-full">
        <div className="p-6 border-b border-slate-800">
          <Link href="/" className="text-xl font-bold text-amber-400 hover:text-amber-300 transition-colors flex items-center gap-2">
            <span>⚡</span> Electrical RCA
          </Link>
          <span className="text-xs text-slate-400 block mt-1">Single-Line Diagram Engine</span>
        </div>
        
        <div className="flex-1 px-4 py-6">
          <div className="space-y-2">
            <Link
              href="/"
              className={`flex items-center px-4 py-3 rounded-lg transition-colors font-semibold ${
                pathname === '/'
                  ? 'bg-amber-400 text-slate-950 shadow-md'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <span className="text-sm font-medium">Single-Line Diagram (SLD)</span>
            </Link>
            <Link
              href="/alerts"
              className={`flex items-center px-4 py-3 rounded-lg transition-colors font-semibold ${
                pathname === '/alerts'
                  ? 'bg-amber-400 text-slate-950 shadow-md'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <span className="text-sm font-medium">SCADA & Relay Alerts</span>
            </Link>
          </div>
        </div>

        <div className="p-4 border-t border-slate-800 text-[11px] text-slate-400">
          Industrial Power System Protection
        </div>
      </div>
    </nav>
  );
}