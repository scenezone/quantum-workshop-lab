import AIChatPanel from '../components/AIChatPanel';
import HardwareLabCallout from '../components/HardwareLabCallout';

export default function Assistant() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold sm:text-4xl">AI Quantum Assistant</h1>
      <p className="mt-2 text-slate-300">
        Continue from your current lesson or experiment, explore its ideas, and understand your results.
      </p>
      <div className="mt-5">
        <HardwareLabCallout compact title="Ask about a real hardware run" description="Open the guided lab to submit an IBM run when available, then bring its live or recorded results back here for an explanation." />
      </div>
      <div className="mt-8">
        <AIChatPanel autoIntroduce />
      </div>
    </div>
  );
}
