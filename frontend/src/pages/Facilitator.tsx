import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Copy, Download, LogOut, RefreshCw } from 'lucide-react';
import { useState } from 'react';
import ErrorMessage from '../components/ErrorMessage';
import {
  createWorkshopSession, fetchFeedbackCsv, fetchFeedbackSummary, fetchSessionDashboard, fetchWorkshopSessions,
  verifyAdminToken,
} from '../services/api';
import { downloadText } from '../services/download';
import type { FeedbackSummary } from '../types/api';

const TOKEN_KEY = 'quantum-workshop-admin-token';

function readToken(): string {
  try {
    return sessionStorage.getItem(TOKEN_KEY) ?? '';
  } catch {
    return '';
  }
}

function storeToken(token: string) {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // The dashboard works for this page even without session storage.
  }
}

function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401) return 'That facilitator token is not valid.';
    if (error.response?.status === 503) return String(error.response.data?.detail ?? 'Facilitator tools are disabled on this server.');
  }
  return 'The request failed. Please try again.';
}

function FeedbackPanel({ summary, title }: { summary: FeedbackSummary; title: string }) {
  const max = Math.max(1, ...Object.values(summary.rating_distribution));
  return (
    <section className="glass p-5" aria-label={title}>
      <h3 className="font-semibold">{title}</h3>
      {summary.count === 0 ? <p className="mt-2 text-sm text-slate-400">No feedback yet.</p> : <>
        <dl className="mt-3 grid gap-3 sm:grid-cols-4">
          <div><dt className="text-xs text-slate-400">Responses</dt><dd className="text-xl font-bold">{summary.count}</dd></div>
          <div><dt className="text-xs text-slate-400">Average rating</dt><dd className="text-xl font-bold">{summary.average_rating?.toFixed(2)}</dd></div>
          <div><dt className="text-xs text-slate-400">Average clarity</dt><dd className="text-xl font-bold">{summary.average_clarity?.toFixed(2)}</dd></div>
          <div><dt className="text-xs text-slate-400">Completed workshop</dt><dd className="text-xl font-bold">{((summary.completion_rate ?? 0) * 100).toFixed(0)}%</dd></div>
        </dl>
        <div className="mt-4 space-y-1" aria-label="Rating distribution">
          {['5', '4', '3', '2', '1'].map((score) => (
            <div key={score} className="flex items-center gap-2 text-xs">
              <span className="w-12 text-slate-400">{score} stars</span>
              <div className="h-2 flex-1 rounded bg-white/10">
                <div className="h-2 rounded bg-cyan-400" style={{ width: `${((summary.rating_distribution[score] ?? 0) / max) * 100}%` }} />
              </div>
              <span className="w-6 text-right">{summary.rating_distribution[score] ?? 0}</span>
            </div>
          ))}
        </div>
        {summary.recent_comments.length > 0 && <ul className="mt-4 max-h-64 space-y-2 overflow-y-auto text-sm">
          {summary.recent_comments.map((item, index) => <li key={index} className="rounded-lg bg-white/5 p-3">
            <p>{item.comments}</p>
            <p className="mt-1 text-xs text-slate-400">{item.rating}/5 · {new Date(item.created_at).toLocaleString()}</p>
          </li>)}
        </ul>}
      </>}
    </section>
  );
}

function Dashboard({ token, code }: { token: string; code: string }) {
  const dashboard = useQuery({
    queryKey: ['session-dashboard', code],
    queryFn: () => fetchSessionDashboard(token, code),
    refetchInterval: 10000,
  });
  const [copied, setCopied] = useState('');
  if (dashboard.isLoading) return <p role="status" className="text-sm text-slate-400">Loading session…</p>;
  if (dashboard.isError || !dashboard.data) return <ErrorMessage message={errorMessage(dashboard.error)} />;
  const data = dashboard.data;
  const joinUrl = `${window.location.origin}/progress?session=${data.session.code}`;
  const maxLesson = Math.max(1, data.participant_count);

  return (
    <div className="space-y-6">
      <section className="glass p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">{data.session.name}</h2>
            <p className="mt-1 text-sm text-slate-400">Ends {new Date(data.session.expires_at).toLocaleString()} · refreshes every 10 seconds</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-400">Session code</p>
            <p className="font-mono text-3xl font-black tracking-widest text-cyan-200">{data.session.code}</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <input className="input max-w-md flex-1 text-xs" readOnly value={joinUrl} aria-label="Participant join link" onFocus={(event) => event.currentTarget.select()} />
          <button type="button" className="btn-secondary text-sm" onClick={() => {
            void navigator.clipboard?.writeText(joinUrl).then(() => setCopied('Link copied.'), () => setCopied('Copy the link from the field.'));
          }}><Copy className="h-4 w-4" /> Copy join link</button>
          <button type="button" className="btn-secondary text-sm" onClick={() => void dashboard.refetch()}><RefreshCw className="h-4 w-4" /> Refresh</button>
          {copied && <span role="status" className="text-xs text-slate-400">{copied}</span>}
        </div>
      </section>

      <section className="glass p-5" aria-label="Participants">
        <h3 className="font-semibold">Participants ({data.participant_count})</h3>
        {data.participants.length === 0 ? <p className="mt-2 text-sm text-slate-400">Nobody has joined yet. Share the code above.</p> :
          <div className="mt-3 overflow-x-auto">
            <table className="w-full min-w-[36rem] text-left text-sm">
              <thead className="text-slate-400"><tr>
                <th className="p-2">Nickname</th><th className="p-2">Lessons</th><th className="p-2">Challenges</th>
                <th className="p-2">Practice</th><th className="p-2">Last active</th>
              </tr></thead>
              <tbody>{data.participants.map((item) => <tr key={item.participant_id} className="border-t border-white/10">
                <td className="p-2 font-medium">{item.nickname}</td>
                <td className="p-2">{item.completed_lessons}</td>
                <td className="p-2">{item.completed_challenges}</td>
                <td className="p-2">{item.practice_correct}/{item.practice_attempted}</td>
                <td className="p-2 text-slate-400">{new Date(item.last_seen).toLocaleTimeString()}</td>
              </tr>)}</tbody>
            </table>
          </div>}
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="glass p-5" aria-label="Lesson completion">
          <h3 className="font-semibold">Lesson completion</h3>
          <ul className="mt-3 space-y-2 text-sm">
            {data.lesson_completion.map((lesson) => <li key={lesson.lesson_id}>
              <div className="flex justify-between gap-3"><span>{lesson.title}</span><span className="text-slate-400">{lesson.completed}/{data.participant_count}</span></div>
              <div className="mt-1 h-1.5 rounded bg-white/10"><div className="h-1.5 rounded bg-purple-400" style={{ width: `${(lesson.completed / maxLesson) * 100}%` }} /></div>
            </li>)}
          </ul>
          {Object.keys(data.challenge_completion).length > 0 && <>
            <h3 className="mt-5 font-semibold">Challenges completed</h3>
            <ul className="mt-2 space-y-1 text-sm">{Object.entries(data.challenge_completion).sort((a, b) => b[1] - a[1]).map(([id, count]) =>
              <li key={id} className="flex justify-between"><span className="font-mono text-xs">{id}</span><span>{count}</span></li>)}
            </ul>
          </>}
        </section>
        <div className="space-y-3">
          <FeedbackPanel summary={data.feedback} title="Feedback from this session" />
          <button type="button" className="btn-secondary text-sm" onClick={() => void fetchFeedbackCsv(token, data.session.code)
            .then((text) => downloadText(`feedback-${data.session.code}.csv`, text, 'text/csv;charset=utf-8'))}>
            <Download className="h-4 w-4" /> Export session feedback (CSV)
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Facilitator() {
  const queryClient = useQueryClient();
  const [token, setToken] = useState(readToken);
  const [draftToken, setDraftToken] = useState('');
  const [sessionName, setSessionName] = useState('Quantum workshop');
  const [selected, setSelected] = useState('');
  const signIn = useMutation({
    mutationFn: (candidate: string) => verifyAdminToken(candidate).then(() => candidate),
    onSuccess: (candidate) => { storeToken(candidate); setToken(candidate); setDraftToken(''); },
  });
  const sessions = useQuery({ queryKey: ['workshop-sessions', token], queryFn: () => fetchWorkshopSessions(token), enabled: Boolean(token) });
  const overall = useQuery({ queryKey: ['feedback-summary', token], queryFn: () => fetchFeedbackSummary(token), enabled: Boolean(token) });
  const create = useMutation({
    mutationFn: () => createWorkshopSession(token, sessionName.trim()),
    onSuccess: (session) => {
      setSelected(session.code);
      void queryClient.invalidateQueries({ queryKey: ['workshop-sessions'] });
    },
  });
  const active = selected || sessions.data?.[0]?.code || '';

  function signOut() {
    storeToken('');
    setToken('');
    queryClient.removeQueries({ queryKey: ['workshop-sessions'] });
  }

  if (!token) {
    return (
      <div className="mx-auto max-w-xl px-4 py-12 sm:px-6">
        <h1 className="text-3xl font-bold">Facilitator Dashboard</h1>
        <p className="mt-3 text-slate-300">
          Create a session code for your workshop, watch participants’ progress live, and review feedback.
          Enter the <code>ADMIN_TOKEN</code> configured on the backend.
        </p>
        <form className="glass mt-6 p-5" onSubmit={(event) => { event.preventDefault(); if (draftToken.trim()) signIn.mutate(draftToken.trim()); }}>
          <label className="text-sm" htmlFor="admin-token">Facilitator token</label>
          <input id="admin-token" type="password" className="input mt-2" autoComplete="current-password" value={draftToken}
            onChange={(event) => setDraftToken(event.target.value)} />
          <p className="mt-2 text-xs text-slate-400">The token is kept only in this browser tab and cleared when you close it.</p>
          <button type="submit" className="btn-primary mt-4" disabled={!draftToken.trim() || signIn.isPending}>
            {signIn.isPending ? 'Checking…' : 'Open dashboard'}
          </button>
          {signIn.isError && <p role="alert" className="mt-3 text-sm text-rose-300">{errorMessage(signIn.error)}</p>}
        </form>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-cyan-300">Facilitator</p>
          <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Workshop Dashboard</h1>
        </div>
        <button type="button" className="btn-secondary text-sm" onClick={signOut}><LogOut className="h-4 w-4" /> Sign out</button>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[18rem_minmax(0,1fr)]">
        <aside className="space-y-4">
          <form className="glass p-4" onSubmit={(event) => { event.preventDefault(); if (sessionName.trim()) create.mutate(); }}>
            <label className="text-sm" htmlFor="session-name">New session name</label>
            <input id="session-name" className="input mt-2" maxLength={80} value={sessionName} onChange={(event) => setSessionName(event.target.value)} />
            <button type="submit" className="btn-primary mt-3 w-full text-sm" disabled={create.isPending || !sessionName.trim()}>
              {create.isPending ? 'Creating…' : 'Create session code'}
            </button>
            {create.isError && <p role="alert" className="mt-2 text-sm text-rose-300">{errorMessage(create.error)}</p>}
          </form>
          <nav className="glass p-4" aria-label="Active sessions">
            <h2 className="text-sm font-semibold">Active sessions</h2>
            {sessions.isError && <p className="mt-2 text-sm text-rose-300">{errorMessage(sessions.error)}</p>}
            {sessions.data?.length === 0 && <p className="mt-2 text-sm text-slate-400">No active sessions yet.</p>}
            <ul className="mt-2 space-y-1">
              {sessions.data?.map((session) => <li key={session.code}>
                <button type="button" onClick={() => setSelected(session.code)} aria-current={active === session.code ? 'true' : undefined}
                  className={`w-full rounded-lg px-3 py-2 text-left text-sm ${active === session.code ? 'bg-cyan-400/10 text-cyan-100' : 'hover:bg-white/5'}`}>
                  <span className="font-mono">{session.code}</span> · {session.name}
                </button>
              </li>)}
            </ul>
          </nav>
          <button type="button" className="btn-secondary w-full text-sm" onClick={() => void fetchFeedbackCsv(token)
            .then((text) => downloadText('workshop-feedback.csv', text, 'text/csv;charset=utf-8'))}>
            <Download className="h-4 w-4" /> Export all feedback
          </button>
        </aside>
        <div className="min-w-0 space-y-6">
          {active ? <Dashboard token={token} code={active} /> : <p className="text-slate-400">Create a session to get a code for participants.</p>}
          {overall.data && <FeedbackPanel summary={overall.data} title="All feedback on this server" />}
        </div>
      </div>
    </div>
  );
}
