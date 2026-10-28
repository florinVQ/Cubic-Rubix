const DEFAULT_VIEW = { yaw: -30, pitch: -20 };
const DEGREES_PER_PIXEL = 0.4;
const YAW_LIMIT = 75;
const PITCH_RANGE = [-60, 20];

const clamp = (value, [min, max]) => Math.min(max, Math.max(min, value));

/** Drag to tilt the cube (the front face with the arrows always stays visible); double-click resets. */
export function enableOrbit(viewport, rig) {
  let { yaw, pitch } = DEFAULT_VIEW;
  let lastPoint = null;

  const render = () => {
    rig.style.setProperty('--yaw', `${yaw}deg`);
    rig.style.setProperty('--pitch', `${pitch}deg`);
  };

  viewport.addEventListener('pointerdown', (event) => {
    if (event.target.closest('.handle')) return;
    viewport.setPointerCapture(event.pointerId);
    lastPoint = [event.clientX, event.clientY];
  });
  viewport.addEventListener('pointermove', (event) => {
    if (!lastPoint) return;
    yaw = clamp(yaw + (event.clientX - lastPoint[0]) * DEGREES_PER_PIXEL, [-YAW_LIMIT, YAW_LIMIT]);
    pitch = clamp(pitch - (event.clientY - lastPoint[1]) * DEGREES_PER_PIXEL, PITCH_RANGE);
    lastPoint = [event.clientX, event.clientY];
    render();
  });
  const stopDragging = () => { lastPoint = null; };
  viewport.addEventListener('pointerup', stopDragging);
  viewport.addEventListener('pointercancel', stopDragging);
  viewport.addEventListener('dblclick', () => {
    ({ yaw, pitch } = DEFAULT_VIEW);
    render();
  });
  render();
}
