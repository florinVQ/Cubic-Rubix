import { movesRows } from './labels.js';

const FACES = ['front', 'back', 'right', 'left', 'up', 'down'];
const QUARTER_TURN = 90;

const easeInOutCubic = (t) => (t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2);

function animate(duration, onFrame) {
  return new Promise((resolve) => {
    const start = performance.now();
    const tick = (now) => {
      const progress = Math.min(1, (now - start) / duration);
      onFrame(progress);
      if (progress < 1) requestAnimationFrame(tick);
      else resolve();
    };
    requestAnimationFrame(tick);
  });
}

/** The 3D cube. Cubies never move; a turn rotates the cubies of a layer, then the stickers are repainted. */
export class CubeScene {
  constructor(rig, cubeElement) {
    this.rig = rig;
    this.cubeElement = cubeElement;
    this.cubies = [];
    this.stickers = [];
  }

  build(size, stickers) {
    this.rig.style.setProperty('--n', size);
    const half = (size - 1) / 2;
    const byPosition = new Map();
    const fragment = document.createDocumentFragment();
    this.cubies = [];

    for (let x = 0; x < size; x++) {
      for (let y = 0; y < size; y++) {
        for (let z = 0; z < size; z++) {
          const element = document.createElement('div');
          element.className = 'cubie';
          const base = `translate3d(calc(var(--s) * ${x - half}), calc(var(--s) * ${y - half}), calc(var(--s) * ${z - half}))`;
          element.style.transform = base;
          const faces = Object.fromEntries(FACES.map((name) => {
            const face = document.createElement('div');
            face.className = `face f-${name}`;
            element.append(face);
            return [name, face];
          }));
          const cubie = { element, base, x, y, z, faces };
          this.cubies.push(cubie);
          byPosition.set(`${x},${y},${z}`, cubie);
          fragment.append(element);
        }
      }
    }
    this.cubeElement.replaceChildren(fragment);

    this.stickers = stickers.map(({ face, row, col, x, y, z }) => {
      const element = document.createElement('i');
      element.className = 'sticker';
      byPosition.get(`${x},${y},${z}`).faces[face].append(element);
      return { element, face, row, col };
    });
  }

  paint(faces) {
    for (const { element, face, row, col } of this.stickers) element.dataset.c = faces[face][row][col];
  }

  highlight(direction, layers) {
    this.clearHighlight();
    for (const cubie of this.#layerCubies(direction, layers)) cubie.element.classList.add('hl');
  }

  clearHighlight() {
    for (const { element } of this.cubies) element.classList.remove('hl');
  }

  /** Rotates the layers one quarter turn, then paints `facesAfter`. */
  async turn(direction, layers, duration, facesAfter) {
    const axis = movesRows(direction) ? 'Y' : 'X';
    const sign = direction === 'right' || direction === 'up' ? 1 : -1;
    const moving = this.#layerCubies(direction, layers);
    await animate(duration, (progress) => {
      const angle = sign * QUARTER_TURN * easeInOutCubic(progress);
      for (const cubie of moving) cubie.element.style.transform = `rotate${axis}(${angle}deg) ${cubie.base}`;
    });
    for (const cubie of moving) cubie.element.style.transform = cubie.base;
    this.paint(facesAfter);
  }

  #layerCubies(direction, layers) {
    const axis = movesRows(direction) ? 'y' : 'x';
    return this.cubies.filter((cubie) => layers.includes(cubie[axis]));
  }
}
