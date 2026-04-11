import { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface TagInputProps {
  label: string;
  hint: string;
  tags: string[];
  onAdd: (tag: string) => void;
  onRemove: (index: number) => void;
  max: number;
}

export function TagInput({ label, hint, tags, onAdd, onRemove, max }: TagInputProps) {
  const [input, setInput] = useState('');
  const [charError, setCharError] = useState<string | null>(null);

  const add = () => {
    const trimmed = input.trim();
    if (trimmed.length > 150) {
      setCharError('Keep it under 150 characters');
      return;
    }
    setCharError(null);
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
      <label className="mb-1 block text-sm font-medium text-off-white">{label}</label>
      <p className="mb-2 text-xs text-off-white/55">{hint}</p>
      <div className="flex gap-2">
        <Input
          type="text"
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            if (charError) setCharError(null);
          }}
          onKeyDown={handleKeyDown}
          disabled={tags.length >= max}
          placeholder={tags.length >= max ? `You've added ${max} items (the max)` : 'Type and press Enter'}
          className="flex-1"
        />
        <Button
          type="button"
          size="sm"
          onClick={add}
          disabled={tags.length >= max || !input.trim()}
          className="bg-accent-orange hover:brightness-110 text-surface-dark border-transparent disabled:opacity-40"
        >
          Add
        </Button>
      </div>
      <p className="mt-1 text-xs text-off-white/40">{tags.length}/{max}</p>
      {charError && <p className="mt-0.5 text-xs text-red-400">{charError}</p>}
      {tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {tags.map((tag, i) => (
            <span
              key={`${tag}-${i}`}
              className="inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium text-off-white"
              style={{ border: '1px solid rgba(245,240,232,0.35)', background: 'rgba(245,240,232,0.1)' }}
            >
              {tag}
              <button
                type="button"
                onClick={() => onRemove(i)}
                className="rounded-full p-0.5 hover:bg-off-white/10 cursor-pointer"
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
