// frontend/src/components/FeedbackForm.tsx
import { Star } from 'lucide-react';
import { useState } from 'react';
import { submitFeedback } from '../services/api';

export default function FeedbackForm() {
  const [rating, setRating] = useState(5);
  const [clarity, setClarity] = useState(5);
  const [completed, setCompleted] = useState(false);
  const [comments, setComments] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setError(null);
    try {
      await submitFeedback({
      rating,
      clarity_rating: clarity,
      completed_workshop: completed,
      comments: comments || undefined,
    });
      setSubmitted(true);
    } catch {
      setError('Feedback could not be submitted. Please try again.');
    } finally {
      setPending(false);
    }
  }

  if (submitted) {
    return <p className="text-sm text-emerald-300">Thank you for your anonymous feedback.</p>;
  }

  return (
    <form onSubmit={submit} className="glass space-y-4 p-5">
      <h2 className="font-semibold">Anonymous feedback</h2>
      <label className="block text-sm">
        Overall rating
        <select className="input mt-2" value={rating} onChange={(e) => setRating(Number(e.target.value))}>
          {[5, 4, 3, 2, 1].map((value) => <option key={value}>{value}</option>)}
        </select>
      </label>
      <label className="block text-sm">
        Clarity rating
        <select className="input mt-2" value={clarity} onChange={(e) => setClarity(Number(e.target.value))}>
          {[5, 4, 3, 2, 1].map((value) => <option key={value}>{value}</option>)}
        </select>
      </label>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={completed} onChange={(e) => setCompleted(e.target.checked)} />
        I completed the workshop
      </label>
      <textarea
        className="input min-h-24"
        maxLength={1000}
        value={comments}
        onChange={(e) => setComments(e.target.value)}
        placeholder="Optional comments"
      />
      {error && <p role="alert" className="text-sm text-rose-300">{error}</p>}
      <button disabled={pending} className="btn-primary"><Star className="h-4 w-4" /> {pending ? 'Submitting...' : 'Submit feedback'}</button>
    </form>
  );
}