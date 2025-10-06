import { useState } from "react";
const API = import.meta.env.VITE_API_BASE || "http://localhost:8080";

export default function App() {
  const [health, setHealth] = useState<string>("");

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API}/health`);
      const data = await res.json();
      setHealth(JSON.stringify(data, null, 2));
    } catch (e:any) {
      setHealth(`Error: ${e?.message || e}`);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
      <div className="max-w-xl w-full p-8 rounded-2xl bg-slate-900/60 backdrop-blur border border-slate-800 shadow">
        <h1 className="text-2xl font-bold mb-4">🔥 NEUE UI – TrainWise Frontend</h1>
        <p className="text-sm text-slate-400 mb-6">
          API Base: <span className="font-mono">{API}</span>
        </p>
        <button
          onClick={checkHealth}
          className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 transition"
        >
          Health prüfen
        </button>
        <pre className="mt-6 text-xs bg-slate-950/60 p-4 rounded-xl overflow-auto">
{health || "Noch kein Request gesendet."}
        </pre>
      </div>
    </div>
  );
}
