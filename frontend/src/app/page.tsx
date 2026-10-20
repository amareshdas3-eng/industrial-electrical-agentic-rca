'use client';

import dynamic from 'next/dynamic';
import SLDVisualization from '@/components/SLDVisualization';

const Neo4jVisualization = dynamic(() => import('@/components/Neo4jVisualization'), {
  ssr: false,
});

export default function Home() {
  return (
    <main className="p-8 min-h-screen bg-slate-950 text-white">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Primary Industrial Single-Line Diagram */}
        <SLDVisualization />

        {/* Neo4j Raw Graph View */}
        <div className="bg-slate-900 rounded-xl shadow-lg p-6 border border-slate-800">
          <h2 className="text-xl font-bold mb-4 text-slate-100 flex items-center gap-2">
            <span>🕸️</span> Neo4j Graph Topology View
          </h2>
          <Neo4jVisualization />
        </div>
      </div>
    </main>
  );
}
