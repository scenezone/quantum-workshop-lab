import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { Users } from 'lucide-react';
import { useState } from 'react';
import { joinSession } from '../services/api';
import { setSessionMembership, syncNow, useSessionMembership } from '../services/session';

const SYNC_LABELS = {
  idle: 'Waiting to sync',
  syncing: 'Syncing…',
  synced: 'Progress shared with your facilitator',
  error: 'Sync failed; it will retry when your progress changes',
  ended: 'This session has ended',
} as const;

export default function SessionJoinCard({ initialCode = '' }: { initialCode?: string }) {
  const { membership, syncState } = useSessionMembership();
  const [code, setCode] = useState(initialCode.toUpperCase());
  const [nickname, setNickname] = useState('');
  const join = useMutation({
    mutationFn: () => joinSession(code.trim(), nickname.trim()),
    onSuccess: (result) => setSessionMembership({
      code: result.session.code,
      name: result.session.name,
      nickname: nickname.trim(),
      participantId: result.participant_id,
      participantToken: result.participant_token,
      expiresAt: result.session.expires_at,
    }),
  });
  const error = join.error && axios.isAxiosError(join.error)
    ? join.error.response?.status === 404 ? 'That session code was not found or has ended.'
      : join.error.response?.status === 503 ? 'Workshop sessions are not enabled on this server.'
        : 'Could not join the session. Please try again.'
    : '';

  return (
    <section className="glass p-5" aria-labelledby="session-title">
      <h2 id="session-title" className="flex items-center gap-2 font-semibold"><Users className="h-5 w-5 text-cyan-400" /> Workshop session</h2>
      {membership ? <div className="mt-3 text-sm">
        <p>You joined <strong>{membership.name}</strong> ({membership.code}) as <strong>{membership.nickname}</strong>.</p>
        <p role="status" className={`mt-1 ${syncState === 'error' || syncState === 'ended' ? 'text-amber-200' : 'text-slate-400'}`}>
          {SYNC_LABELS[syncState]}
        </p>
        <p className="mt-2 text-xs text-slate-400">
          Your facilitator sees your nickname, completed lessons and challenges, and practice score. Nothing else is shared.
        </p>
        <div className="mt-3 flex flex-wrap gap-3">
          <button type="button" className="btn-secondary text-sm" onClick={() => void syncNow()}>Sync now</button>
          <button type="button" className="btn-secondary text-sm" onClick={() => setSessionMembership(null)}>Leave session</button>
        </div>
      </div> : <form className="mt-3" onSubmit={(event) => { event.preventDefault(); if (code.trim() && nickname.trim()) join.mutate(); }}>
        <p className="text-sm text-slate-300">If your facilitator gave you a code, join to share your progress with them.</p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <label className="text-sm">Session code
            <input className="input mt-2 font-mono uppercase" maxLength={12} value={code} autoComplete="off"
              onChange={(event) => setCode(event.target.value.toUpperCase())} />
          </label>
          <label className="text-sm">Nickname
            <input className="input mt-2" maxLength={40} value={nickname} placeholder="Shown to your facilitator"
              onChange={(event) => setNickname(event.target.value)} />
          </label>
        </div>
        <p className="mt-2 text-xs text-slate-400">Use a nickname rather than your full name.</p>
        <button type="submit" className="btn-primary mt-3 text-sm" disabled={!code.trim() || !nickname.trim() || join.isPending}>
          {join.isPending ? 'Joining…' : 'Join session'}
        </button>
        {error && <p role="alert" className="mt-2 text-sm text-rose-300">{error}</p>}
      </form>}
    </section>
  );
}
