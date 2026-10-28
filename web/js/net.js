import { FACE_NAMES } from './labels.js';

const CELL_GAP_PX = 2;
const BLOCK_GAP_PX = 8;
const MIN_CELL_PX = 6;
const MAX_CELL_PX = 28;
const SLIDE_EASING = 'cubic-bezier(.65, 0, .35, 1)';
// [column, row] of each face in the unfolded cross: Front Right Back Left in a band, Up above Front, Down below it.
const LAYOUT = { up: [1, 1], front: [1, 2], right: [2, 2], back: [3, 2], left: [4, 2], down: [1, 3] };

const cellKey = (face, row, col) => `${face}:${row}:${col}`;

/** The unfolded cube. Cells that move slide from their old position to the new one. */
export class NetView {
  constructor(root) {
    this.root = root;
    this.size = 0;
    this.cells = new Map();
    root.style.setProperty('--cell-gap', `${CELL_GAP_PX}px`);
    root.style.setProperty('--block-gap', `${BLOCK_GAP_PX}px`);
    new ResizeObserver(() => this.#fit()).observe(root);
  }

  build(size) {
    this.size = size;
    this.cells.clear();
    this.root.style.setProperty('--n', size);
    const blocks = Object.entries(LAYOUT).map(([face, [column, row]]) => {
      const block = document.createElement('div');
      block.className = 'block';
      block.style.gridColumn = column;
      block.style.gridRow = row;
      const name = document.createElement('span');
      name.className = 'face-name';
      name.textContent = FACE_NAMES[face];
      const grid = document.createElement('div');
      grid.className = 'grid';
      for (let r = 0; r < size; r++) {
        for (let c = 0; c < size; c++) {
          const slot = document.createElement('div');
          slot.className = 'slot';
          const cell = document.createElement('div');
          cell.className = 'cell';
          slot.append(cell);
          grid.append(slot);
          this.cells.set(cellKey(face, r, c), { slot, cell });
        }
      }
      block.append(name, grid);
      return block;
    });
    this.root.replaceChildren(...blocks);
    this.#fit();
  }

  setFaces(faces) {
    for (const [key, { cell }] of this.cells) {
      const [face, row, col] = key.split(':');
      const value = faces[face][row][col];
      cell.dataset.c = value;
      cell.dataset.v = value;
    }
  }

  setDetailed(isDetailed) {
    this.root.classList.toggle('detailed', isDetailed);
  }

  /** Paints `faces`, then slides every moved cell from its old slot into its new one. */
  async slide(transfers, duration, faces) {
    this.setFaces(faces);
    const slides = transfers.map(([source, destination]) => {
      const from = this.#slot(source).getBoundingClientRect();
      const to = this.#slot(destination).getBoundingClientRect();
      const { cell } = this.cells.get(cellKey(...destination));
      cell.classList.add('moving');
      const animation = cell.animate(
        [{ transform: `translate(${from.left - to.left}px, ${from.top - to.top}px)` }, { transform: 'translate(0, 0)' }],
        { duration, easing: SLIDE_EASING },
      );
      return animation.finished.then(() => cell.classList.remove('moving'));
    });
    await Promise.all(slides);
  }

  #slot([face, row, col]) {
    return this.cells.get(cellKey(face, row, col)).slot;
  }

  #fit() {
    const width = this.root.clientWidth;
    if (!width || !this.size) return;
    const gaps = 3 * BLOCK_GAP_PX + 4 * (this.size - 1) * CELL_GAP_PX;
    const cell = Math.floor((width - gaps) / (4 * this.size));
    this.root.style.setProperty('--cell', `${Math.max(MIN_CELL_PX, Math.min(MAX_CELL_PX, cell))}px`);
  }
}
