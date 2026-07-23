import { useEffect, useRef, useState, useCallback } from "react";

const POLL_INTERVAL_MS = 8000;

function timeAgo(isoString) {
  if (!isoString) return "—";

  // SQLite returns timestamps without timezone.
  // Assume they are UTC.
  const normalized =
    isoString.endsWith("Z")
      ? isoString
      : isoString + "Z";

  const date = new Date(normalized);

  if (Number.isNaN(date.getTime()))
    return "—";

  const diff = Math.floor(
    (Date.now() - date.getTime()) / 1000
  );

  if (diff < 5) return "just now";
  if (diff < 60) return `${diff}s ago`;

  const minutes = Math.floor(diff / 60);
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  return `${Math.floor(hours / 24)}d ago`;
}

function StatusPill({ isUp }) {
  if (isUp === null || isUp === undefined) {
    return (
      <span className="pill pill--pending">
        <span className="dot dot--pending" />
        PENDING
      </span>
    );
  }
  return isUp ? (
    <span className="pill pill--up">
      <span className="dot dot--up" />
      UP
    </span>
  ) : (
    <span className="pill pill--down">
      <span className="dot dot--down" />
      DOWN
    </span>
  );
}

export default function App() {
  const [urls, setUrls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newUrl, setNewUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);
  const [busyRowId, setBusyRowId] = useState(null);
  const [selectedUrl, setSelectedUrl] = useState(null);
const [history, setHistory] = useState([]);
const [historyLoading, setHistoryLoading] = useState(false);
const [historyError, setHistoryError] = useState(null);
  const pollRef = useRef(null);

  async function openHistory(url) {
  setSelectedUrl(url);
  setHistory([]);
  setHistoryLoading(true);
  setHistoryError(null);

  try {
    const res = await fetch(`/urls/${url.id}/history`);

    if (!res.ok) {
      throw new Error("Failed to fetch history.");
    }

    const data = await res.json();
    setHistory(data);

  } catch (err) {
    setHistoryError(err.message);
  } finally {
    setHistoryLoading(false);
  }
}

function closeHistory() {
  setSelectedUrl(null);
  setHistory([]);
}

  const fetchUrls = useCallback(async ({ silent } = {}) => {
    try {
      if (!silent) setLoading(true);
      const res = await fetch("/urls/");
      if (!res.ok) throw new Error(`Server responded ${res.status}`);
      const data = await res.json();
      setUrls(data);
      setError(null);
    } catch (err) {
      setError("Can't reach the monitor API. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUrls();
    pollRef.current = setInterval(() => fetchUrls({ silent: true }), POLL_INTERVAL_MS);
    return () => clearInterval(pollRef.current);
  }, [fetchUrls]);

  async function handleAddUrl(e) {
    e.preventDefault();
    setFormError(null);

    let candidate = newUrl.trim();
    if (!candidate) return;
    if (!/^https?:\/\//i.test(candidate)) candidate = `https://${candidate}`;

    setSubmitting(true);
    try {
      const res = await fetch("/urls/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: candidate }),
      });
      if (!res.ok) {
        if (res.status === 409) throw new Error("That URL is already being monitored.");
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Server responded ${res.status}`);
      }
      setNewUrl("");
      await fetchUrls({ silent: true });
    } catch (err) {
      setFormError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCheckNow(id) {
    setBusyRowId(id);
    try {
      await fetch(`/urls/${id}/check-now`, { method: "POST" });
      await fetchUrls({ silent: true });
    } finally {
      setBusyRowId(null);
    }
  }

  async function handleDelete(id) {
    setBusyRowId(id);
    try {
      await fetch(`/urls/${id}`, { method: "DELETE" });
      await fetchUrls({ silent: true });
    } finally {
      setBusyRowId(null);
    }
  }

  const upCount = urls.filter((u) => u.is_up === true).length;
  const downCount = urls.filter((u) => u.is_up === false).length;

  return (
    <div className="page">
      <header className="header">
        <div className="header__title">
          <span className="header__pulse" aria-hidden="true" />
          <h1>Pulse</h1>
        </div>
        <p className="header__subtitle">A quiet room that watches your endpoints so you don't have to.</p>
        <div className="header__stats">
          <span><strong>{urls.length}</strong> monitored</span>
          <span className="stat--up"><strong>{upCount}</strong> up</span>
          <span className="stat--down"><strong>{downCount}</strong> down</span>
        </div>
      </header>

      <form className="add-form" onSubmit={handleAddUrl}>
        <input
          type="text"
          placeholder="https://example.com"
          value={newUrl}
          onChange={(e) => setNewUrl(e.target.value)}
          aria-label="URL to monitor"
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Adding…" : "Add URL"}
        </button>
      </form>
      {formError && <p className="form-error">{formError}</p>}

      <main className="board">
        {loading && urls.length === 0 && <p className="empty">Loading monitors…</p>}
        {error && <p className="empty empty--error">{error}</p>}
        {!loading && !error && urls.length === 0 && (
          <p className="empty">
            Nothing being watched yet. Add a URL above — try{" "}
            <code>https://example.com</code> for an easy win, and something like{" "}
            <code>https://this-domain-does-not-exist-xyz.com</code> to see a DOWN state.
          </p>
        )}

        {urls.length > 0 && (
          <table className="board__table">
            <thead>
              <tr>
                <th>Status</th>
                <th>URL</th>
                <th>Code</th>
                <th>Response</th>
                <th>Last checked</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {urls.map((u) => (
                <tr key={u.id} className={busyRowId === u.id ? "row--busy" : ""}>
                  <td><StatusPill isUp={u.is_up} /></td>
                  <td>
                    <div className="url-cell">
                      <a href={u.url} target="_blank" rel="noreferrer">{u.url}</a>
                    </div>
                  </td>
                  <td className="mono">{u.status_code ?? "—"}</td>
                  <td className="mono">{u.response_time_ms != null ? `${u.response_time_ms} ms` : "—"}</td>
                  <td className="mono muted">{timeAgo(u.last_checked_at)}</td>
                  <td>
                    <div className="row-actions">

    <button
        className="btn-ghost"
        onClick={() => openHistory(u)}
        title="History"
    >
        📈
    </button>

    <button
        className="btn-ghost"
        onClick={() => handleCheckNow(u.id)}
        disabled={busyRowId === u.id}
    >
        ↻
    </button>

    <button
        className="btn-ghost btn-ghost--danger"
        onClick={() => handleDelete(u.id)}
        disabled={busyRowId === u.id}
    >
        ✕
    </button>

    {selectedUrl && (
  <div className="modal-overlay" onClick={closeHistory}>
    <div
      className="modal"
      onClick={(e) => e.stopPropagation()}
    >
      <div className="modal-header">
        <h2>History</h2>

        <button
          className="btn-ghost"
          onClick={closeHistory}
        >
          ✕
        </button>
      </div>

      <p className="modal-url">{selectedUrl.url}</p>

      {historyLoading && <p>Loading...</p>}

      {historyError && (
        <p className="form-error">
          {historyError}
        </p>
      )}

      {!historyLoading && history.length === 0 && (
        <p>No checks yet.</p>
      )}

      {!historyLoading && history.length > 0 && (
        <table className="history-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Code</th>
              <th>Response</th>
              <th>Checked</th>
            </tr>
          </thead>

          <tbody>
            {history.map((h) => (
              <tr key={h.id}>
                <td>
                  <StatusPill isUp={h.is_up} />
                </td>

                <td>{h.status_code ?? "—"}</td>

                <td>
                  {h.response_time_ms != null
                    ? `${h.response_time_ms} ms`
                    : "—"}
                </td>

                <td>{timeAgo(h.checked_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  </div>
)}

</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </main>

      <footer className="footer">
        Checks run automatically every 60s · dashboard refreshes every {POLL_INTERVAL_MS / 1000}s
      </footer>
    </div>
  );
}
