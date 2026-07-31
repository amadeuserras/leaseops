import Link from 'next/link';

export default function RunsIndexPage() {
  return (
    <div className="flex h-full items-center justify-center p-9">
      <div className="max-w-md text-center">
        <h1 className="mb-2 text-[18px] font-bold tracking-[-0.01em]">No run selected</h1>
        <p className="text-ink/55 mb-5 text-[13px] leading-relaxed">
          Pick a message in the inbox to run the agent and watch its trace stream node by node.
        </p>
        <Link
          href="/inbox"
          className="bg-accent inline-flex items-center rounded-md px-4 py-2 text-[13px] font-semibold text-white transition-opacity hover:opacity-90"
        >
          Go to inbox
        </Link>
      </div>
    </div>
  );
}
