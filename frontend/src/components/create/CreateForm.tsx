import { useState, useCallback } from 'react';
import { X, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
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
  label,
  hint,
  tags,
  onAdd,
  onRemove,
  max,
}: {
  label: string;
  hint: string;
  tags: string[];
  onAdd: (tag: string) => void;
  onRemove: (index: number) => void;
  max: number;
}) {
  const [input, setInput] = useState('');

  const add = () => {
    const trimmed = input.trim();
    if (trimmed && tags.length < max) {
      onAdd(trimmed);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      add();
    }
  };

  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-brand-text">{label}</label>
      <p className="mb-2 text-xs text-brand-muted">{hint}</p>
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={tags.length >= max}
          placeholder={tags.length >= max ? `Maximum ${max} items` : 'Type and press Enter'}
          className="flex-1 rounded-md border border-brand-border px-3 py-2 text-sm text-brand-text outline-none focus:border-brand-light focus:ring-1 focus:ring-brand-light"
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={add}
          disabled={tags.length >= max || !input.trim()}
        >
          Add
        </Button>
      </div>
      {tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {tags.map((tag, i) => (
            <span
              key={`${tag}-${i}`}
              className="inline-flex items-center gap-1 rounded-full bg-brand/10 px-3 py-1 text-xs font-medium text-brand"
            >
              {tag}
              <button
                type="button"
                onClick={() => onRemove(i)}
                className="rounded-full p-0.5 hover:bg-brand/20"
                aria-label={`Remove ${tag}`}
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
      await onSubmit({
        topic: topic.trim(),
        misconceptions,
        constraints,
        examples,
        number_of_scenes: numberOfScenes,
      });
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
    <form onSubmit={handleSubmit} className="mx-auto max-w-2xl space-y-6">
      {/* Suggestions box */}
      <div className="rounded-lg border border-brand-border bg-brand/5 p-4">
        <button
          type="button"
          onClick={() => setTipsOpen(!tipsOpen)}
          className="flex w-full items-center justify-between text-sm font-medium text-brand"
        >
          <span>Need inspiration? See an example brief</span>
          {tipsOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {tipsOpen && (
          <div className="mt-3 space-y-2 text-sm text-brand-muted">
            <p><strong>Topic:</strong> {EXAMPLE_BRIEF.topic}</p>
            <p><strong>Misconception:</strong> {EXAMPLE_BRIEF.misconceptions[0]}</p>
            <p><strong>Constraint:</strong> {EXAMPLE_BRIEF.constraints[0]}</p>
            <p><strong>Example:</strong> {EXAMPLE_BRIEF.examples[0]}</p>
            <p><strong>Scenes:</strong> {EXAMPLE_BRIEF.number_of_scenes}</p>
            <Button type="button" variant="outline" size="sm" onClick={fillExample}>
              Use this example
            </Button>
          </div>
        )}
      </div>

      {/* Topic */}
      <div>
        <label htmlFor="topic" className="mb-1 block text-sm font-medium text-brand-text">
          Topic <span className="text-red-500">*</span>
        </label>
        <input
          id="topic"
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          maxLength={200}
          required
          placeholder="E.g., Solving linear equations, The Pythagorean theorem, Understanding fractions"
          className="w-full rounded-md border border-brand-border px-3 py-2 text-sm text-brand-text outline-none focus:border-brand-light focus:ring-1 focus:ring-brand-light"
        />
        <p className="mt-1 text-xs text-brand-muted">{topic.length}/200</p>
      </div>

      {/* Misconceptions */}
      <TagInput
        label="Misconceptions"
        hint="Common mistakes students make — e.g., Confusing numerator and denominator"
        tags={misconceptions}
        onAdd={(tag) => setMisconceptions((prev) => [...prev, tag])}
        onRemove={(i) => setMisconceptions((prev) => prev.filter((_, idx) => idx !== i))}
        max={5}
      />

      {/* Constraints */}
      <TagInput
        label="Constraints"
        hint="Style or content rules — e.g., Use only visual animations, Avoid heavy notation"
        tags={constraints}
        onAdd={(tag) => setConstraints((prev) => [...prev, tag])}
        onRemove={(i) => setConstraints((prev) => prev.filter((_, idx) => idx !== i))}
        max={5}
      />

      {/* Examples */}
      <TagInput
        label="Examples"
        hint="Concrete examples to include — e.g., 2x + 3 = 7, A 3-4-5 right triangle"
        tags={examples}
        onAdd={(tag) => setExamples((prev) => [...prev, tag])}
        onRemove={(i) => setExamples((prev) => prev.filter((_, idx) => idx !== i))}
        max={5}
      />

      {/* Number of Scenes */}
      <div>
        <label htmlFor="scenes" className="mb-1 block text-sm font-medium text-brand-text">
          Number of Scenes <span className="text-red-500">*</span>
        </label>
        <p className="mb-2 text-xs text-brand-muted">
          How many scenes to render. Each scene takes 2-3 minutes.
        </p>
        <input
          id="scenes"
          type="number"
          value={numberOfScenes}
          onChange={(e) => setNumberOfScenes(Math.min(3, Math.max(1, parseInt(e.target.value) || 1)))}
          min={1}
          max={3}
          className="w-24 rounded-md border border-brand-border px-3 py-2 text-sm text-brand-text outline-none focus:border-brand-light focus:ring-1 focus:ring-brand-light"
        />
      </div>

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <Button
        type="submit"
        disabled={!isValid || submitting}
        className="w-full bg-brand-accent py-3 text-base font-semibold text-white hover:bg-brand-accent/90 disabled:opacity-50"
        size="lg"
      >
        {submitting ? 'Submitting...' : 'Generate My Lesson Video \u2192'}
      </Button>
    </form>
  );
}
