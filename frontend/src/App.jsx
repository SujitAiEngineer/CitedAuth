import { useState } from "react";

const API_BASE = "http://localhost:8000";
const TRUNCATE_AT = 25;

function TruncatedCell({ text, onShowMore }) {
  if (!text) return <span>-</span>;
  if (text.length <= TRUNCATE_AT) return <span>{text}</span>;
  return (
    <span>
      {text.slice(0, TRUNCATE_AT)}
      <button
        onClick={onShowMore}
        style={{
          border: "none", background: "none", color: "#0060df",
          cursor: "pointer", padding: 0, marginLeft: 2, font: "inherit",
        }}
      >
        ...show more
      </button>
    </span>
  );
}

function TextModal({ title, text, onClose }) {
  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)",
        display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "white", borderRadius: 6, padding: "1.25rem",
          maxWidth: "700px", maxHeight: "80vh", overflow: "auto", width: "90%",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <strong>{title}</strong>
          <button onClick={onClose} style={{ cursor: "pointer" }}>Close</button>
        </div>
        <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", fontSize: "0.8rem", margin: 0 }}>
          {text}
        </pre>
      </div>
    </div>
  );
}

export default function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState([]);
  const [usage, setUsage] = useState(null);
  const [latencyMs, setLatencyMs] = useState(null);
  const [selected, setSelected] = useState(new Set());
  const [letterNote, setLetterNote] = useState(null);
  const [modal, setModal] = useState(null);

  async function handleAnalyze() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setLetterNote(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed: ${res.status}`);
      }
      const data = await res.json();
      setResults(data.results);
      setUsage(data.usage);
      setLatencyMs(data.latency_ms);
      setSelected(new Set());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function toggleRow(requestId) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(requestId)) next.delete(requestId);
      else next.add(requestId);
      return next;
    });
  }

  function selectAll() {
    setSelected(new Set(results.map((r) => r.request_id)));
  }

  function deselectAll() {
    setSelected(new Set());
  }

  async function handleGenerateLetters() {
    setLetterNote(null);
    try {
      const selectedRows = results.filter((r) => selected.has(r.request_id));
      const res = await fetch(`${API_BASE}/api/letters/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(selectedRows),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed: ${res.status}`);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "prior_auth_letters.pdf";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setLetterNote(e.message);
    }
  }

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", maxWidth: 960, margin: "2rem auto", padding: "0 1rem" }}>
      <h1 style={{ fontSize: "1.4rem" }}>Prior Auth Review</h1>

      <section style={{ display: "flex", gap: "0.75rem", alignItems: "center", margin: "1rem 0" }}>
        <input
          type="file"
          accept=".xlsx"
          onChange={(e) => setFile(e.target.files[0] || null)}
        />
        <button onClick={handleAnalyze} disabled={!file || loading}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </section>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {usage && (
        <p style={{ color: "#555", fontSize: "0.9rem" }}>
          input tokens: {usage.input_tokens} · output tokens: {usage.output_tokens} ·
          latency: {latencyMs.toFixed(0)} ms
        </p>
      )}

      {results.length > 0 && (
        <>
          <div style={{ display: "flex", gap: "0.5rem", margin: "0.5rem 0" }}>
            <button onClick={selectAll}>Select all</button>
            <button onClick={deselectAll}>Deselect all</button>
            <button onClick={handleGenerateLetters} disabled={selected.size === 0}>
              Generate letters (PDF)
            </button>
          </div>

          {letterNote && <p style={{ color: "#a05a00" }}>{letterNote}</p>}

          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "2px solid #ccc" }}>
                <th></th>
                <th>ID</th>
                <th>Member</th>
                <th>Procedure</th>
                <th>Determination</th>
                <th>Policy</th>
                <th>Criterion</th>
                <th>Reason</th>
                <th>Urgent</th>
                <th>LLM Input</th>
                <th>LLM Output</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.request_id} style={{ borderBottom: "1px solid #eee" }}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selected.has(r.request_id)}
                      onChange={() => toggleRow(r.request_id)}
                    />
                  </td>
                  <td>{r.request_id}</td>
                  <td>{r.member_id}</td>
                  <td>{r.procedure}</td>
                  <td>{r.determination}</td>
                  <td>{r.policy_id || "-"}</td>
                  <td>{r.criterion || "-"}</td>
                  <td>{r.reason}</td>
                  <td>{r.urgent ? "yes" : ""}</td>
                  <td>
                    <TruncatedCell
                      text={r.llm_input}
                      onShowMore={() =>
                        setModal({ title: `LLM input - request #${r.request_id}`, text: r.llm_input })
                      }
                    />
                  </td>
                  <td>
                    <TruncatedCell
                      text={r.llm_output}
                      onShowMore={() =>
                        setModal({ title: `LLM output - request #${r.request_id}`, text: r.llm_output })
                      }
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {modal && <TextModal title={modal.title} text={modal.text} onClose={() => setModal(null)} />}
    </div>
  );
}
