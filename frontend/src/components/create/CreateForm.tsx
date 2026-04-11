import { useState, useCallback, useRef } from 'react';
import { Shuffle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { TagInput } from './TagInput';
import type { UserRequest } from '@/services/api';

interface CreateFormProps {
  onSubmit: (request: UserRequest) => Promise<void>;
  error: string | null;
}

const EXAMPLE_BRIEFS: UserRequest[] = [
  {
    topic: 'One-Step Equations',
    misconceptions: ['Students think you can change one side without doing the same to the other'],
    constraints: ['Use a visual balance scale', 'Show the inverse operation clearly'],
    examples: ['x + 7 = 12', '3x = 15'],
    number_of_scenes: 1,
  },
  {
    topic: 'Order of Operations (PEMDAS)',
    misconceptions: [
      'Students evaluate left to right without respecting precedence',
      'Students forget exponents come before multiplication',
    ],
    constraints: ['Keep a PEMDAS reference on screen throughout', 'Highlight only the step being evaluated'],
    examples: ['4 + 2(5 - x) with x = 3', '3(2 + x)² with x = 1'],
    number_of_scenes: 1,
  },
  {
    topic: 'Two-Step Equations',
    misconceptions: [
      'Students undo operations in the wrong order',
      'Students forget to apply the operation to both sides',
    ],
    constraints: ['Label each inverse operation step', 'Show both sides changing together'],
    examples: ['2x + 3 = 11', 'x/4 - 1 = 2'],
    number_of_scenes: 2,
  },
  {
    topic: 'Factoring Quadratics',
    misconceptions: [
      'Students mix up which pairs multiply to c and add to b',
      'Students forget sign rules for factor pairs',
    ],
    constraints: ['Show the product and sum conditions side by side', 'Use color to track a, b, and c'],
    examples: ['x² + 5x + 6', 'x² - x - 6'],
    number_of_scenes: 2,
  },
  {
    topic: 'The Quadratic Formula',
    misconceptions: [
      'Students only divide the square root by 2a, not the whole numerator',
      'Students make sign errors under the radical',
    ],
    constraints: ['Highlight each part of the formula as it gets substituted', 'Show both the positive and negative roots'],
    examples: ['2x² + 4x - 6 = 0'],
    number_of_scenes: 2,
  },
];

export function CreateForm({ onSubmit, error }: CreateFormProps) {
  const [topic, setTopic] = useState('');
  const [misconceptions, setMisconceptions] = useState<string[]>([]);
  const [constraints, setConstraints] = useState<string[]>([]);
  const [examples, setExamples] = useState<string[]>([]);
  const [numberOfScenes, setNumberOfScenes] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const lastExampleIndex = useRef<number>(-1);

  const isValid = topic.trim().length > 0 && topic.length <= 200 && numberOfScenes >= 1 && numberOfScenes <= 3;

  const handleSubmit = useCallback(async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!isValid || submitting) return;
    setSubmitting(true);
    try {
      await onSubmit({ topic: topic.trim(), misconceptions, constraints, examples, number_of_scenes: numberOfScenes });
    } finally {
      setSubmitting(false);
    }
  }, [isValid, submitting, topic, misconceptions, constraints, examples, numberOfScenes, onSubmit]);

  const fillRandomExample = () => {
    let idx;
    do {
      idx = Math.floor(Math.random() * EXAMPLE_BRIEFS.length);
    } while (idx === lastExampleIndex.current && EXAMPLE_BRIEFS.length > 1);
    lastExampleIndex.current = idx;

    const brief = EXAMPLE_BRIEFS[idx];
    setTopic(brief.topic);
    setMisconceptions([...brief.misconceptions]);
    setConstraints([...brief.constraints]);
    setExamples([...brief.examples]);
    setNumberOfScenes(brief.number_of_scenes);
  };

  return (
    <div className="mx-auto max-w-2xl">
      <div className="rounded-xl shadow-lg" style={{ border: '1px solid rgba(245,240,232,0.15)', background: 'rgba(245,240,232,0.05)' }}>
        <form onSubmit={handleSubmit} className="py-10 px-10 space-y-6">

          {/* Topic */}
          <div>
            <label htmlFor="topic" className="mb-1 block text-sm font-medium text-off-white">
              Topic <span className="text-red-400">*</span>
            </label>
            <p className="mb-2 text-xs text-off-white/55">
              What concept should the video teach? Be as specific as you like.
            </p>
            <Input
              id="topic"
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              maxLength={200}
              required
              placeholder="e.g. Solving linear equations, The Pythagorean theorem, Understanding fractions"
            />
            <p className="mt-1 text-xs text-off-white/40">{topic.length}/200</p>
          </div>

          <TagInput
            label="Misconceptions"
            hint="What mistakes do students often make with this topic? This helps the video address them head-on."
            tags={misconceptions}
            onAdd={(tag) => setMisconceptions(p => [...p, tag])}
            onRemove={(i) => setMisconceptions(p => p.filter((_, idx) => idx !== i))}
            max={5}
          />

          <TagInput
            label="Constraints"
            hint="Any style or content rules you want to enforce, like using only visual animations or avoiding heavy notation."
            tags={constraints}
            onAdd={(tag) => setConstraints(p => [...p, tag])}
            onRemove={(i) => setConstraints(p => p.filter((_, idx) => idx !== i))}
            max={5}
          />

          <TagInput
            label="Examples"
            hint="Specific problems or cases you want the video to walk through, like 2x + 3 = 7 or a 3-4-5 right triangle."
            tags={examples}
            onAdd={(tag) => setExamples(p => [...p, tag])}
            onRemove={(i) => setExamples(p => p.filter((_, idx) => idx !== i))}
            max={5}
          />

          {/* Number of Scenes */}
          <div>
            <label htmlFor="scenes" className="mb-1 block text-sm font-medium text-off-white">
              Number of Scenes <span className="text-red-400">*</span>
            </label>
            <p className="mb-2 text-xs text-off-white/55">
              Each scene takes about 1 to 2 minutes to render. Start with 1 if you're just exploring.
            </p>
            <Input
              id="scenes"
              type="number"
              value={numberOfScenes}
              onChange={(e) => setNumberOfScenes(Math.min(3, Math.max(1, parseInt(e.target.value) || 1)))}
              min={1}
              max={3}
              className="w-20"
            />
          </div>

          {error && (
            <div
              className="rounded-md p-3 text-sm text-red-400"
              style={{ background: 'rgba(220,38,38,0.12)', border: '1px solid rgba(220,38,38,0.4)' }}
            >
              {error}
            </div>
          )}

          <div className="flex items-center gap-3 pt-1">
            <Button
              type="submit"
              disabled={!isValid || submitting}
              size="lg"
              className="bg-accent-orange hover:brightness-110 text-surface-dark border-transparent"
            >
              {submitting ? 'Submitting...' : 'Generate My Lesson Video! \u2192'}
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="lg"
              onClick={fillRandomExample}
              className="bg-off-white/10 text-off-white/85 hover:bg-off-white/15 hover:text-off-white gap-1.5"
            >
              <Shuffle className="h-4 w-4" />
              Try an example
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
