"use client";

import { upload } from "@vercel/blob/client";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";

type User = { username: string; email: string };
type Message = {
  role: "user" | "assistant";
  content: string;
  created_at?: string;
  id?: string;
};
type DocumentInfo = {
  name: string;
  chunk_count: number;
  character_count: number;
  uploaded_at?: string;
};
type ApiError = { detail?: string; error?: string };

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(path, {
    ...init,
    headers,
    credentials: "include",
    cache: "no-store",
  });
  const body: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = body as ApiError;
    throw new Error(error.detail || error.error || "Something went wrong.");
  }
  return body as T;
}

function safeFilename(filename: string): string {
  return filename
    .normalize("NFKC")
    .replace(/[^A-Za-z0-9._-]+/g, "_")
    .replace(/^\.+/, "")
    .slice(-120) || "study-material.txt";
}

export default function Workspace() {
  const [user, setUser] = useState<User | null>(null);
  const [document, setDocument] = useState<DocumentInfo | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [authBusy, setAuthBusy] = useState(false);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [chatBusy, setChatBusy] = useState(false);
  const [error, setError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  const loadWorkspace = useCallback(async () => {
    const [documentResult, historyResult] = await Promise.all([
      requestJson<{ document: DocumentInfo | null }>("/api/document"),
      requestJson<{ messages: Message[] }>("/api/chat/history"),
    ]);
    setDocument(documentResult.document);
    setMessages(historyResult.messages.map((message) => ({
      ...message,
      id: crypto.randomUUID(),
    })));
  }, []);

  useEffect(() => {
    let active = true;
    requestJson<{ user: User }>("/api/me")
      .then(async ({ user: signedInUser }) => {
        if (!active) return;
        setUser(signedInUser);
        await loadWorkspace();
      })
      .catch((reason: unknown) => {
        if (reason instanceof Error && !reason.message.includes("sign in")) {
          setError(reason.message);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [loadWorkspace]);

  async function submitAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthBusy(true);
    setError("");
    try {
      const path = authMode === "register" ? "/api/auth/register" : "/api/auth/login";
      const body = authMode === "register"
        ? { username, email, password }
        : { username, password };
      const result = await requestJson<{ user: User }>(path, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setUser(result.user);
      setPassword("");
      await loadWorkspace();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not sign in.");
    } finally {
      setAuthBusy(false);
    }
  }

  async function signOut() {
    setError("");
    try {
      await requestJson("/api/auth/logout", { method: "POST" });
      setUser(null);
      setDocument(null);
      setMessages([]);
      setPassword("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not sign out.");
    }
  }

  async function processFile(file: File) {
    if (!user) return;
    if (file.size > 25 * 1024 * 1024) {
      setError("File is too large. Maximum size is 25 MB.");
      return;
    }
    const name = safeFilename(file.name);
    setUploadBusy(true);
    setError("");
    try {
      const result = await upload(
        `edith/${user.username}/${crypto.randomUUID()}-${name}`,
        file,
        {
          access: "private",
          handleUploadUrl: "/blob-upload",
        },
      );
      const processed = await requestJson<{ document: DocumentInfo }>(
        "/api/document/process",
        {
          method: "POST",
          body: JSON.stringify({ pathname: result.pathname, filename: name }),
        },
      );
      setDocument(processed.document);
      setMessages([]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not process this file.");
    } finally {
      setUploadBusy(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = draft.trim();
    if (!question || chatBusy) return;
    const userMessage: Message = {
      role: "user",
      content: question,
      id: crypto.randomUUID(),
    };
    setMessages((current) => [...current, userMessage]);
    setDraft("");
    setChatBusy(true);
    setError("");
    try {
      const result = await requestJson<{ answer: string }>("/api/chat", {
        method: "POST",
        body: JSON.stringify({ question }),
      });
      setMessages((current) => [
        ...current,
        { role: "assistant", content: result.answer, id: crypto.randomUUID() },
      ]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The AI could not answer.");
    } finally {
      setChatBusy(false);
    }
  }

  if (loading) {
    return <main className="loading-screen"><span className="brand-mark">E</span><p>Opening your study studio…</p></main>;
  }

  if (!user) {
    return (
      <main className="auth-page">
        <section className="auth-story">
          <div className="brand"><span className="brand-mark">E</span><span>EcoEdith<small>AI learning studio</small></span></div>
          <p className="eyebrow">STUDY WITH MORE CLARITY</p>
          <h1>Make every study session count.</h1>
          <p className="story-copy">Bring your materials and turn questions into clear explanations, useful practice, and confident learning.</p>
          <div className="story-orbit" aria-hidden="true"><span>🧠</span><i /><b /></div>
          <p className="story-footer">Document-aware answers · Notes and practice · Your personal study space</p>
        </section>

        <section className="auth-card">
          <p className="eyebrow">YOUR PERSONAL LEARNING SPACE</p>
          <h2>{authMode === "login" ? "Welcome to EcoEdith" : "Create your account"}</h2>
          <p className="muted">{authMode === "login" ? "Sign in to pick up where your learning begins." : "Save your materials and learning progress."}</p>
          <div className="auth-tabs" role="tablist" aria-label="Account action">
            <button type="button" className={authMode === "login" ? "active" : ""} onClick={() => { setAuthMode("login"); setError(""); }}>Sign in</button>
            <button type="button" className={authMode === "register" ? "active" : ""} onClick={() => { setAuthMode("register"); setError(""); }}>Create account</button>
          </div>
          <form className="auth-form" onSubmit={submitAuth}>
            <label>Username<input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required minLength={3} maxLength={30} placeholder="Letters, numbers, underscore" /></label>
            {authMode === "register" && <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required placeholder="you@example.com" /></label>}
            <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={authMode === "login" ? "current-password" : "new-password"} required minLength={authMode === "register" ? 8 : 1} maxLength={128} placeholder={authMode === "register" ? "At least 8 characters" : "Enter your password"} /></label>
            {error && <p className="error-message" role="alert">{error}</p>}
            <button className="button button-primary full-width" type="submit" disabled={authBusy}>
              {authBusy ? "Please wait…" : authMode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>
          <p className="privacy-note">Your account and study files are stored securely.</p>
        </section>
      </main>
    );
  }

  return (
    <main className="studio">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">E</span><span>EcoEdith<small>AI learning assistant</small></span></div>
        <div className="nav-section">
          <p>STUDY</p>
          <a className="nav-link active" href="#workspace"><span>✦</span>AI chat</a>
          <button className="nav-link" onClick={() => fileInput.current?.click()}><span>▤</span>Upload materials</button>
          <a className="nav-link" href="#workspace"><span>◷</span>Chat history</a>
        </div>
        <div className="sidebar-bottom">
          <span className="avatar">{user.username.slice(0, 1).toUpperCase()}</span>
          <span className="user-label"><strong>{user.username}</strong><small>LEARNER</small></span>
          <button className="icon-button" onClick={signOut} aria-label="Sign out" title="Sign out">↗</button>
        </div>
      </aside>

      <section className="workspace" id="workspace">
        <header className="topbar">
          <div><p className="eyebrow">YOUR PERSONAL AI TUTOR</p><h1>What would you like to learn?</h1></div>
          <div className="topbar-badge"><span>✦</span>AI study studio</div>
        </header>

        <div className="workspace-grid">
          <section className="chat-panel glass-panel">
            <div className="panel-heading">
              <div><h2>✦ EcoEdith</h2><p>{document ? `${document.name} · ${document.chunk_count} sections connected` : "General AI chat · Upload a file to add study context"}</p></div>
              <span className="status-pill"><i /> Ready</span>
            </div>

            <div className="messages" aria-live="polite">
              {messages.length === 0 ? (
                <div className="empty-chat"><span className="empty-icon">✧</span><h3>Start with a question</h3><p>Ask about your material or explore any topic. EcoEdith combines document information with general AI knowledge.</p></div>
              ) : messages.map((message, index) => (
                <article className={`message ${message.role}`} key={message.id ?? `${message.role}-${index}`}>
                  <span className="message-avatar">{message.role === "assistant" ? "E" : user.username.slice(0, 1).toUpperCase()}</span>
                  <div><small>{message.role === "assistant" ? "EcoEdith" : "You"}</small><p>{message.content}</p></div>
                </article>
              ))}
              {chatBusy && <p className="thinking"><span className="pulse-dot" /> Looking through your study material…</p>}
            </div>

            {error && <p className="error-message inline-error" role="alert">{error}</p>}
            <form className="chat-form" onSubmit={submitQuestion}>
              <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Ask a question about your studies…" aria-label="Message EcoEdith" maxLength={4000} disabled={chatBusy} />
              <button className="send-button" type="submit" disabled={!draft.trim() || chatBusy} aria-label="Send message">↑</button>
            </form>
            <p className="chat-disclaimer">AI can make mistakes. Check important information against your source material.</p>
          </section>

          <aside className="tools-panel">
            <section className="glass-panel upload-card">
              <div className="card-icon">▤</div>
              <p className="eyebrow">YOUR STUDY MATERIAL</p>
              <h2>{document ? "Replace document" : "Add a document"}</h2>
              <p className="muted">Upload a PDF, DOCX or TXT file. Your tutor will use its contents when relevant.</p>
              <input ref={fileInput} className="file-input" type="file" accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain" onChange={(event) => { const file = event.target.files?.[0]; if (file) void processFile(file); }} />
              <button className="button button-primary full-width" onClick={() => fileInput.current?.click()} disabled={uploadBusy}>
                {uploadBusy ? "Uploading and indexing…" : document ? "Choose another file" : "Choose a file"}
              </button>
              <small className="file-hint">PDF · DOCX · TXT · up to 25 MB</small>
            </section>

            <section className="glass-panel tip-card">
              <span className="tip-icon">✧</span>
              <p className="eyebrow">A GOOD QUESTION</p>
              <p>“Explain the key idea in simple terms and give me an example.”</p>
            </section>

            <div className="feature-tags"><span>Private files</span><span>Document-aware AI</span><span>Saved chat</span></div>
          </aside>
        </div>
      </section>
    </main>
  );
}
