import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { checkPracticeAnswer } from '../services/api';
import type { PracticeFeedback, PracticeQuestion } from '../types/api';
import Markdown from './Markdown';

function QuestionCard({ lessonId, question, number, onResult }: {
  lessonId: string;
  question: PracticeQuestion;
  number: number;
  onResult: (id: string, result?: PracticeFeedback) => void;
}) {
  const [option, setOption] = useState('');
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState<PracticeFeedback>();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const request = useRef<AbortController | null>(null);
  const multipleChoice = question.kind === 'multiple_choice';
  useEffect(() => () => request.current?.abort(), []);

  function clearFeedback() {
    setFeedback(undefined);
    setError('');
    onResult(question.question_id);
  }

  async function check(event: React.FormEvent) {
    event.preventDefault();
    if (request.current || (multipleChoice ? !option : !answer.trim())) return;
    const controller = new AbortController();
    request.current = controller;
    setPending(true);
    setError('');
    try {
      const result = await checkPracticeAnswer(lessonId, {
        question_id: question.question_id,
        ...(multipleChoice ? { option_id: option } : { answer: answer.trim() }),
      }, controller.signal);
      if (controller.signal.aborted) return;
      setFeedback(result);
      onResult(question.question_id, result);
    } catch (cause) {
      if (controller.signal.aborted || axios.isCancel(cause)) return;
      setError('Your answer could not be checked. Please try again.');
    } finally {
      request.current = null;
      if (!controller.signal.aborted) setPending(false);
    }
  }

  return (
    <form onSubmit={check} aria-labelledby={`${question.question_id}-prompt`} className="min-w-0 rounded-xl border border-white/10 bg-navy-950/40 p-4 sm:p-5">
      <fieldset disabled={pending} className="min-w-0">
        <legend id={`${question.question_id}-prompt`} className="mb-4 w-full text-base font-semibold leading-relaxed">
          <span className="mb-2 block text-xs font-normal text-cyan-300">Question {number}</span>
          <Markdown>{question.prompt}</Markdown>
        </legend>
        {multipleChoice ? <div className="space-y-3">
          {question.options.map(item => {
            const correct = feedback?.kind === 'multiple_choice' && feedback.correct_option_id === item.option_id;
            const wrong = feedback?.kind === 'multiple_choice' && !feedback.correct && option === item.option_id;
            return <label key={item.option_id} className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 text-sm leading-relaxed transition sm:p-4 ${
              correct ? 'border-emerald-400/50 bg-emerald-400/10' : wrong ? 'border-rose-400/50 bg-rose-400/10'
                : option === item.option_id ? 'border-cyan-400/50 bg-cyan-400/10' : 'border-white/10 hover:bg-white/5'
            }`}>
              <input type="radio" name={question.question_id} value={item.option_id} checked={option === item.option_id}
                className="mt-1 h-4 w-4 shrink-0 accent-cyan-400" onChange={() => { setOption(item.option_id); clearFeedback(); }} />
              <span className="min-w-0 flex-1"><Markdown>{item.text}</Markdown>
                {correct && <span className="mt-1 block font-semibold text-emerald-300">Correct option</span>}
                {wrong && <span className="mt-1 block font-semibold text-rose-300">Your selection</span>}
              </span>
            </label>;
          })}
        </div> : <label className="block text-sm text-slate-300">
          Your answer
          <textarea className="input mt-2 min-h-32 resize-y" maxLength={2000} value={answer}
            placeholder="Explain your reasoning before comparing with the sample."
            onChange={event => { setAnswer(event.target.value); clearFeedback(); }} />
        </label>}
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button type="submit" className="btn-primary px-4 text-sm"
            disabled={pending || Boolean(feedback) || (multipleChoice ? !option : !answer.trim())}>
            {pending ? 'Checking…' : multipleChoice ? 'Check answer' : 'Compare with sample answer'}
          </button>
          {feedback && <button type="button" className="btn-secondary px-4 text-sm" onClick={() => {
            setOption(''); setAnswer(''); clearFeedback();
          }}>Try again</button>}
        </div>
      </fieldset>
      {error && <p role="alert" className="mt-3 text-sm text-rose-300">{error}</p>}
      {feedback && <div role="status" className="mt-4 rounded-xl border border-white/10 bg-white/5 p-4 text-sm leading-relaxed">
        {feedback.kind === 'multiple_choice' ? <>
          <p className={`mb-2 font-semibold ${feedback.correct ? 'text-emerald-300' : 'text-amber-300'}`}>
            {feedback.correct ? 'Correct!' : 'Not quite — review the explanation and try again.'}
          </p>
          <Markdown>{feedback.explanation}</Markdown>
        </> : <>
          <h5 className="mb-2 font-semibold text-cyan-300">Sample answer</h5>
          <Markdown>{feedback.sample_answer}</Markdown>
          <h5 className="mb-2 mt-4 font-semibold">Check your reasoning</h5>
          <ul className="list-disc space-y-2 pl-5 text-slate-300">
            {feedback.key_points.map(point => <li key={point}>{point}</li>)}
          </ul>
          <p className="mt-3 text-xs text-slate-400">Compare the ideas with your own words. Written answers are for self-review and are not automatically graded.</p>
        </>}
      </div>}
    </form>
  );
}

export default function LessonPractice({ lessonId, questions }: { lessonId: string; questions: PracticeQuestion[] }) {
  const [results, setResults] = useState<Record<string, PracticeFeedback | undefined>>({});
  const multipleChoice = questions.filter(question => question.kind === 'multiple_choice');
  const written = questions.filter(question => question.kind === 'short_answer');
  const checked = Object.values(results).filter(result => result?.kind === 'multiple_choice');
  const correct = checked.filter(result => result?.kind === 'multiple_choice' && result.correct).length;

  function record(id: string, result?: PracticeFeedback) {
    setResults(current => ({ ...current, [id]: result }));
  }

  return <section className="mt-8 min-w-0 border-t border-white/10 pt-6" aria-label="Topic practice">
    <h3 className="text-xl font-bold">Practice this topic</h3>
    <p className="mt-2 text-sm leading-relaxed text-slate-300">
      Select an option before checking each answer. For written questions, explain your reasoning first, then compare it with the sample.
    </p>
    {multipleChoice.length > 0 && <div className="mt-6">
      <h4 className="font-semibold">Multiple choice · {multipleChoice.length} questions</h4>
      <p className="mb-4 mt-1 text-sm text-cyan-300" aria-live="polite">{correct} of {multipleChoice.length} correct · {checked.length} checked</p>
      <div className="space-y-4">{multipleChoice.map((question, index) => <QuestionCard key={question.question_id}
        lessonId={lessonId} question={question} number={index + 1} onResult={record} />)}</div>
    </div>}
    {written.length > 0 && <div className="mt-8">
      <h4 className="mb-4 font-semibold">Written practice · {written.length} questions</h4>
      <div className="space-y-4">{written.map((question, index) => <QuestionCard key={question.question_id}
        lessonId={lessonId} question={question} number={index + 1} onResult={record} />)}</div>
    </div>}
  </section>;
}
