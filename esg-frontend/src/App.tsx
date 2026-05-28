import { useState, useEffect } from 'react';

type ReviewRecord = {
  id: string;
  status: string;
  data_quality_flags: string[];
  raw_payload: unknown;
};

export default function App() {
  const [records, setRecords] = useState<ReviewRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('https://breathe-esg-vx7s.onrender.com/api/v1/dashboard/pending-review/')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch data');
        return res.json();
      })
      .then((data: ReviewRecord[]) => {
        setRecords(data);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen px-4 py-8 text-zinc-100 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8 border-b border-white/10 pb-4">
          <h1 className="text-3xl font-medium tracking-[-0.03em] text-zinc-50 sm:text-4xl">
            Data Quality <span className="font-semibold text-teal-300">Review</span>
          </h1>
          <p className="mt-2 text-sm text-zinc-400">
            The following records failed automated ingestion and require analyst sign-off before audit lock.
          </p>
        </header>

        {loading && <div className="text-teal-300 animate-pulse">Establishing pipeline connection...</div>}
        {error && <div className="rounded-lg border border-red-500/30 bg-red-950/60 p-4 text-red-200">{error}</div>}

        {!loading && !error && (
          <div className="overflow-hidden rounded-2xl border border-white/10 bg-zinc-950/85 shadow-[0_24px_80px_rgba(0,0,0,0.55)] backdrop-blur-sm">
            <div className="overflow-x-auto">
              <table className="w-full whitespace-nowrap text-left text-sm">
                <thead className="border-b border-white/10 bg-white/5 text-xs uppercase tracking-[0.2em] text-zinc-400">
                  <tr>
                    <th className="px-6 py-4 font-semibold">Row ID</th>
                    <th className="px-6 py-4 font-semibold">Status</th>
                    <th className="px-6 py-4 font-semibold">Quality Flags (Errors)</th>
                    <th className="px-6 py-4 font-semibold">Source Payload Snapshot</th>
                    <th className="px-6 py-4 text-right font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {records.map((record) => (
                    <tr key={record.id} className="transition-colors hover:bg-white/5">
                      <td className="px-6 py-4">
                        <div className="font-mono text-xs text-zinc-400">
                          {record.id.split('-')[0]}...
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <span className="inline-flex items-center rounded-full border border-amber-400/20 bg-amber-400/10 px-2.5 py-0.5 text-xs font-medium text-amber-300">
                          {record.status.replace('_', ' ')}
                        </span>
                      </td>

                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-2">
                          {record.data_quality_flags.map((flag, idx) => (
                            <span
                              key={idx}
                              className="inline-flex items-center rounded-md border border-rose-400/20 bg-rose-500/10 px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-rose-300"
                            >
                              ⚠️ {flag.replace(/_/g, ' ')}
                            </span>
                          ))}
                        </div>
                      </td>

                      <td className="max-w-xs px-6 py-4 font-mono text-xs text-zinc-500 truncate">
                        {JSON.stringify(record.raw_payload)}
                      </td>

                      <td className="px-6 py-4 text-right">
                        <button className="rounded border border-teal-400/30 bg-teal-400/10 px-4 py-1.5 text-xs font-semibold text-teal-300 transition-all hover:bg-teal-300 hover:text-zinc-950">
                          Resolve
                        </button>
                      </td>
                    </tr>
                  ))}

                  {records.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-6 py-12 text-center text-zinc-500">
                        No records pending review. The pipeline is clear.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}