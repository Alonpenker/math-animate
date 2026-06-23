import type { JobStatus } from '@/services/api';

export const LOADER_MESSAGES: Partial<Record<JobStatus, string[]>> = {
  CREATED: [
    'Initializing your lesson...',
    'Setting up the workspace...',
    'Sharpening the chalk and clearing the board...',
    'Getting everything ready for a smooth start...',
    'Reserving compute for the render ahead...',
  ],
  PLANNING: [
    'Crafting your video plan...',
    'Consulting the curriculum...',
    'Designing scenes for maximum clarity...',
    'Mapping out the visual journey...',
    'Sketching the lesson one step at a time...',
    'Lining up the concepts for a clean explanation...',
    'Choosing which ideas deserve their own scene...',
  ],
  APPROVED: [
    'Preparing code generation...',
    'Translating the plan into motion...',
    'Turning the blueprint into animation instructions...',
    'Handing the storyboard to the animator...',
  ],
  CODEGEN: [
    'Writing Manim animation code...',
    'Crafting mathematical animations...',
    'Building the visual sequences...',
    'Converting ideas into precise scene logic...',
    'Teaching the renderer how each moment should unfold...',
    'Positioning every shape, label, and transform...',
  ],
  CODED: [
    'Code ready, starting verification...',
    'The animation script is in place and under review...',
    'Checking that every scene is ready for the next step...',
  ],
  VERIFYING: [
    'Checking animation syntax...',
    'Running quality checks...',
    'Making sure the math and motion stay in sync...',
    'Inspecting each scene before it hits the screen...',
    'Compiling a dry run to catch issues early...',
  ],
  FIXING: [
    'Fixing up a few things...',
    'The AI is polishing the animations...',
    'Tidying the rough edges behind the scenes...',
    'Adjusting details so the lesson flows cleanly...',
    'Reconciling the code with the original plan...',
  ],
  VERIFIED: [
    'Starting the renderer...',
    'Everything looks solid. Sending it to render...',
    'The lesson is cleared for production...',
  ],
  RENDERING: [
    'Rendering your video...',
    'Animating mathematical concepts...',
    'Creating your masterpiece...',
    'This is the exciting part...',
    'Putting the final chalk strokes on the lesson...',
    'Bringing the board to life frame by frame...',
    'Encoding the final cut...',
  ],
};

export const FALLBACK_MESSAGES: string[] = [
  'Working...',
  'Crunching the numbers...',
  'Hang tight, almost there...',
  'Lining things up behind the scenes...',
];
