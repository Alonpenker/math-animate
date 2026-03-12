import { useState, useCallback } from 'react';
import { X, ChevronDown, ChevronUp } from 'lucide-react';
import type { UserRequest } from '@/services/api';

interface CreateFormProps {
  onSubmit: (request: UserRequest) => Promise<void>;
  error: string | null;
}

const EXAMPLE_BRIEF: UserRequest = {
  topic: 'The Pythagorean theorem',
  misconceptions: ['Students think it works for all triangles, not just right triangles'],
  constraints: ['Use only visual animations with labeled sides'],
  examples: ['A 3-4-5 right triangle'],
  number_of_scenes: 2,
};

function TagInput({
  label, hint, tags, onAdd, onRemove, max,
}: {
  label: string; hint: string; tags: string[];
  onAdd: (tag: string) => void; onRemove: (index: number) => void; max: number;
}) {
  const [input, setInput] = useState('');
  const add = () => {
    const trimmed = input.trim();
    if (trimmed && tags.length < max) { onAdd(trimmed); setInput(''); }
  };
  const handleKeyDown = (e: React.KeyboardEvent) => { if (e.key === 'Enter') { e.preventDefault(); add(); } };

  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-chalk-white" style={{ fontFamily: 'Inter, sans-serif' }}>
        {label}
      </label>
      <p className="mb-2 text-xs text-chalk-white/55" style={{ fontFamily: 'Inter, sans-serif' }}>{hint}</p>
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={tags.length >= max}
          placeholder={tags.length >= max ? `Maximum ${max} items` : 'Type and press Enter'}
          className="chalk-input-dark flex-1"
          style={{ fontFamily: 'Inter, sans-serif' }}
        />
        <button
          type="button"
          onClick={add}
          disabled={tags.length >= max || !input.trim()}
          className="rounded-md border border-chalk-white/30 px-3 py-1 text-sm text-chalk-white transition-colors hover:bg-chalk-white/10 disabled:opacity-40 cursor-pointer"
          style={{ fontFamily: 'Inter, sans-serif', background: 'transparent' }}
        >
          Add
        </button>
      </div>
      {tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {tags.map((tag, i) => (
            <span
              key={`${tag}-${i}`}
              className="inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium text-chalk-white"
              style={{ border: '1px solid rgba(245,240,232,0.35)', background: 'rgba(245,240,232,0.1)', fontFamily: 'Inter, sans-serif' }}
            >
              {tag}
              <button
                type="button"
                onClick={() => onRemove(i)}
                className="rounded-full p-0.5 hover:bg-chalk-white/10 cursor-pointer"
                aria-label={`Remove ${tag}`}
                style={{ background: 'none', border: 'none' }}
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export function CreateForm({ onSubmit, error }: CreateFormProps) {
  const [topic, setTopic] = useState('');
  const [misconceptions, setMisconceptions] = useState<string[]>([]);
  const [constraints, setConstraints] = useState<string[]>([]);
  const [examples, setExamples] = useState<string[]>([]);
  const [numberOfScenes, setNumberOfScenes] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [tipsOpen, setTipsOpen] = useState(false);

  const isValid = topic.trim().length > 0 && topic.length <= 200 && numberOfScenes >= 1 && numberOfScenes <= 3;

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid || submitting) return;
    setSubmitting(true);
    try {
      await onSubmit({ topic: topic.trim(), misconceptions, constraints, examples, number_of_scenes: numberOfScenes });
    } finally {
      setSubmitting(false);
    }
  }, [isValid, submitting, topic, misconceptions, constraints, examples, numberOfScenes, onSubmit]);

  const fillExample = () => {
    setTopic(EXAMPLE_BRIEF.topic);
    setMisconceptions([...EXAMPLE_BRIEF.misconceptions]);
    setConstraints([...EXAMPLE_BRIEF.constraints]);
    setExamples([...EXAMPLE_BRIEF.examples]);
    setNumberOfScenes(EXAMPLE_BRIEF.number_of_scenes);
  };

  return (
    <div className="mx-auto max-w-2xl">
      {/* Suggestions box — outside the form / notebook paper */}
      <div
        className="rounded-md p-4 mb-6"
        style={{ border: '1px solid rgba(245,240,232,0.2)', background: 'rgba(245,240,232,0.06)' }}
      >
        <button
          type="button"
          onClick={() => setTipsOpen(!tipsOpen)}
          className="flex w-full items-center justify-between text-sm font-medium text-chalk-white cursor-pointer"
          style={{ fontFamily: 'Inter, sans-serif', background: 'none', border: 'none' }}
        >
          <span>Need inspiration? See an example brief</span>
          {tipsOpen ? <ChevronUp className="h-4 w-4 text-chalk-white/60" /> : <ChevronDown className="h-4 w-4 text-chalk-white/60" />}
        </button>
        {tipsOpen && (
          <div className="mt-3 space-y-2 text-sm text-chalk-white/70" style={{ fontFamily: 'Inter, sans-serif' }}>
            <p><strong>Topic:</strong> {EXAMPLE_BRIEF.topic}</p>
            <p><strong>Misconception:</strong> {EXAMPLE_BRIEF.misconceptions[0]}</p>
            <p><strong>Constraint:</strong> {EXAMPLE_BRIEF.constraints[0]}</p>
            <p><strong>Example:</strong> {EXAMPLE_BRIEF.examples[0]}</p>
            <p><strong>Scenes:</strong> {EXAMPLE_BRIEF.number_of_scenes}</p>
            <button
              type="button"
              onClick={fillExample}
              className="mt-2 rounded-md border border-chalk-white/30 px-3 py-1 text-sm text-chalk-white hover:bg-chalk-white/10 cursor-pointer"
              style={{ fontFamily: 'Inter, sans-serif', background: 'transparent' }}
            >
              Use this example
            </button>
          </div>
        )}
      </div>

      <div className="rounded-xl shadow-lg" style={{ border: '1px solid rgba(245,240,232,0.15)', background: 'rgba(245,240,232,0.05)' }}>
        <form onSubmit={handleSubmit} className="py-10 px-10 space-y-6">

      {/* Topic */}
      <div>
        <label htmlFor="topic" className="mb-1 block text-sm font-medium text-chalk-white" style={{ fontFamily: 'Inter, sans-serif' }}>
          Topic <span className="text-red-400">*</span>
        </label>
        <input
          id="topic"
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          maxLength={200}
          required
          placeholder="E.g., Solving linear equations, The Pythagorean theorem, Understanding fractions"
          className="chalk-input-dark"
          style={{ fontFamily: 'Inter, sans-serif' }}
        />
        <p className="mt-1 text-xs text-chalk-white/40">{topic.length}/200</p>
      </div>

      <TagInput label="Misconceptions" hint="Common mistakes students make — e.g., Confusing numerator and denominator"
        tags={misconceptions} onAdd={(tag) => setMisconceptions(p => [...p, tag])} onRemove={(i) => setMisconceptions(p => p.filter((_, idx) => idx !== i))} max={5} />
      <TagInput label="Constraints" hint="Style or content rules — e.g., Use only visual animations, Avoid heavy notation"
        tags={constraints} onAdd={(tag) => setConstraints(p => [...p, tag])} onRemove={(i) => setConstraints(p => p.filter((_, idx) => idx !== i))} max={5} />
      <TagInput label="Examples" hint="Concrete examples to include — e.g., 2x + 3 = 7, A 3-4-5 right triangle"
        tags={examples} onAdd={(tag) => setExamples(p => [...p, tag])} onRemove={(i) => setExamples(p => p.filter((_, idx) => idx !== i))} max={5} />

      <div>
        <label htmlFor="scenes" className="mb-1 block text-sm font-medium text-chalk-white" style={{ fontFamily: 'Inter, sans-serif' }}>
          Number of Scenes <span className="text-red-400">*</span>
        </label>
        <p className="mb-2 text-xs text-chalk-white/55" style={{ fontFamily: 'Inter, sans-serif' }}>
          How many scenes to render. Each scene takes 2-3 minutes.
        </p>
        <input
          id="scenes"
          type="number"
          value={numberOfScenes}
          onChange={(e) => setNumberOfScenes(Math.min(3, Math.max(1, parseInt(e.target.value) || 1)))}
          min={1}
          max={3}
          className="chalk-input-dark"
          style={{ width: 80, fontFamily: 'Inter, sans-serif' }}
        />
      </div>

      {error && (
        <div
          className="rounded-md p-3 text-sm text-red-400"
          style={{ background: 'rgba(220,38,38,0.12)', border: '1px solid rgba(220,38,38,0.4)', fontFamily: 'Inter, sans-serif' }}
        >
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={!isValid || submitting}
        className="rounded-[10px] border-2 border-chalk-orange text-chalk-orange px-8 py-3 text-lg transition-all hover:bg-chalk-orange hover:text-white disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        style={{ fontFamily: 'Patrick Hand, cursive' }}
      >
        {submitting ? 'Submitting...' : 'Generate My Lesson Video \u2192'}
      </button>
        </form>
      </div>
    </div>
  );
}
