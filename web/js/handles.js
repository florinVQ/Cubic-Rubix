import { movesRows } from './labels.js';

const HANDLE_GAP_PX = 30;
const SIDES = [
  { direction: 'left', edge: -1 },
  { direction: 'right', edge: 1 },
  { direction: 'up', edge: -1 },
  { direction: 'down', edge: 1 },
];
const AXIS_NAMES = { row: 'Rândul', col: 'Coloana' };
const DIRECTION_NAMES = { left: 'spre stânga', right: 'spre dreapta', up: 'în sus', down: 'în jos' };
const ARROW_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>';

/** Arrow buttons around the front face: left/right per row, up/down per column. */
export function buildHandles(container, size, { onPress, onHover, onLeave }) {
  const half = (size - 1) / 2;
  const buttons = [];
  for (const { direction, edge } of SIDES) {
    const isRow = movesRows(direction);
    for (let index = 0; index < size; index++) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = `handle handle-${direction}`;
      button.dataset.lock = '';
      button.innerHTML = ARROW_ICON;
      button.setAttribute('aria-label', `${AXIS_NAMES[isRow ? 'row' : 'col']} ${index + 1} ${DIRECTION_NAMES[direction]}`);

      const along = `calc(var(--s) * ${index - half})`;
      const outward = `calc(var(--cube) * ${edge * 0.5} + ${edge * HANDLE_GAP_PX}px)`;
      const [x, y] = isRow ? [outward, along] : [along, outward];
      button.style.transform = `translate3d(${x}, ${y}, calc(var(--cube) * 0.5))`;

      button.addEventListener('click', () => onPress(direction, index));
      button.addEventListener('pointerenter', () => onHover(direction, index));
      button.addEventListener('pointerleave', onLeave);
      button.addEventListener('focus', () => onHover(direction, index));
      button.addEventListener('blur', onLeave);
      buttons.push(button);
    }
  }
  container.replaceChildren(...buttons);
}
