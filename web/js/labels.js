export const FACE_NAMES = {
  up: 'Sus', front: 'Față', right: 'Dreapta', back: 'Spate', left: 'Stânga', down: 'Jos',
};

const ARROWS = { right: '→', left: '←', up: '↑', down: '↓' };
const ORIGIN_TAGS = { scramble: 'amestecare', solve: 'auto-resolve', manual: '' };

export const movesRows = (direction) => direction === 'right' || direction === 'left';

export function describeMove({ direction, layer, width, times }) {
  const axis = movesRows(direction) ? 'Rând' : 'Coloană';
  const layers = width === 1 ? `${layer + 1}` : `${layer + 1}–${layer + width}`;
  return `${times}× ${axis} ${layers} ${ARROWS[direction]}`;
}

export const describeStep = (moves) => moves.map(describeMove).join('  +  ');
export const originTag = (origin) => ORIGIN_TAGS[origin] ?? '';
