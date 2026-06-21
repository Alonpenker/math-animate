export interface StoryboardPhase {
  header: string;
  description: string;
}

export type ParseStoryboardResult =
  | { ok: true; phases: StoryboardPhase[] }
  | { ok: false; error: 'invalid_format' };

const PHASE_HEADER_PATTERN = /^Phase \d+: (.+)$/;
const PHASE_LIKE_PATTERN = /^phase\s+\d+/i;

export function parseStoryboard(raw: string): ParseStoryboardResult {
  const lines = raw.replace(/\r\n/g, '\n').trim().split('\n');
  const phases: StoryboardPhase[] = [];
  let lineIndex = 0;

  while (lineIndex < lines.length) {
    while (lineIndex < lines.length && lines[lineIndex].trim() === '') {
      lineIndex += 1;
    }

    if (lineIndex >= lines.length) {
      break;
    }

    const header = lines[lineIndex];
    const headerMatch = PHASE_HEADER_PATTERN.exec(header);
    if (!headerMatch || headerMatch[1].trim() === '') {
      return { ok: false, error: 'invalid_format' };
    }

    lineIndex += 1;
    const descriptionLines: string[] = [];

    while (lineIndex < lines.length && !PHASE_HEADER_PATTERN.test(lines[lineIndex])) {
      if (PHASE_LIKE_PATTERN.test(lines[lineIndex].trim())) {
        return { ok: false, error: 'invalid_format' };
      }
      descriptionLines.push(lines[lineIndex]);
      lineIndex += 1;
    }

    const description = descriptionLines.join('\n').trim();
    if (!description) {
      return { ok: false, error: 'invalid_format' };
    }

    phases.push({ header, description });
  }

  return phases.length > 0
    ? { ok: true, phases }
    : { ok: false, error: 'invalid_format' };
}
