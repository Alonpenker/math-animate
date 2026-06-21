import type { UserRequest } from '@/services/api';

export const EXAMPLE_BRIEFS: UserRequest[] = [
  {
    topic: 'Pythagorean Theorem by Area Rearrangement',
    misconceptions: [
      'Students see a² + b² = c² as a formula rather than an area relationship',
    ],
    constraints: [
      'Rearrange four identical right triangles inside one outer square to compare the c² square with the a² and b² squares',
    ],
    examples: ['Use a 3-4-5 right triangle'],
    number_of_scenes: 1,
  },
  {
    topic: 'Derivative as the Limit of Secant Slopes',
    misconceptions: [
      'Students confuse the slope of a secant line with the slope of a tangent line',
    ],
    constraints: [
      'Plot f(x)=x², move one secant point toward x=1, and finish by emphasizing the tangent line at x=1',
    ],
    examples: ['Estimate the derivative of f(x)=x² at x=1'],
    number_of_scenes: 1,
  },
  {
    topic: 'Horizontal and Vertical Function Translations',
    misconceptions: [
      'Students think f(x-h) shifts a graph left',
      'Students confuse horizontal shifts with vertical shifts',
    ],
    constraints: [
      'Keep fixed axes and move the parabola and its vertex from f(x)=x² to g(x)=(x-2)²-1',
    ],
    examples: ['Translate f(x)=x² right 2 units and down 1 unit'],
    number_of_scenes: 1,
  },
  {
    topic: 'Matrix Multiplication as Row-Column Dot Products',
    misconceptions: [
      'Students multiply corresponding matrix entries instead of taking dot products',
      'Students think matrix multiplication is commutative',
    ],
    constraints: [
      'Highlight each selected row and column, show its dot product, and reveal the corresponding result cell',
    ],
    examples: ['Multiply [[1,2],[3,4]] by [[2,0],[1,2]]'],
    number_of_scenes: 1,
  },
  {
    topic: 'Sine and Cosine on the Unit Circle',
    misconceptions: [
      'Students treat sine and cosine as unrelated formulas instead of coordinates',
      'Students lose the signs of coordinates outside the first quadrant',
    ],
    constraints: [
      'Rotate the radius to 150°, reveal the reference triangle and coordinate projections, and emphasize quadrant II',
    ],
    examples: ['Find sin(150°) and cos(150°)'],
    number_of_scenes: 1,
  },
];
