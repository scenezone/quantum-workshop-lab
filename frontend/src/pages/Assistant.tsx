import AIChatPanel from '../components/AIChatPanel';

export default function Assistant() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold sm:text-4xl">AI Quantum Assistant</h1>
      <p className="mt-2 text-slate-300">
        Continue from your current lesson or experiment, explore its ideas, and understand your results.
      </p>
      <div className="mt-8">
        <AIChatPanel autoIntroduce />
      </div>
    </div>
  );
}
