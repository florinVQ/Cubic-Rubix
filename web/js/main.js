import { api } from './api.js';
import { buildHandles } from './handles.js';
import { describeMove, describeStep, FACE_NAMES, originTag } from './labels.js';
import { NetView } from './net.js';
import { enableOrbit } from './orbit.js';
import { CubeScene } from './scene3d.js';

const SIZES = [2, 3, 4, 5, 6, 7, 8];
const DEFAULT_SIZE = 3;
const QUARTER_TURN_DEGREES = 90;
const MIN_SPEED = 30;
const MAX_SPEED = 720;
const STEP_PAUSE_MS = 450;
const TOAST_MS = 3200;
const MAX_TIMES = 9;
const MAX_LOGGED_TRANSFERS = 8;
const SCRAMBLE_STEPS = 10;

const $ = (id) => document.getElementById(id);
const ui = {
  rig: $('rig'), cube: $('cube'), handles: $('handles'), viewport: $('viewport'),
  hud: { number: $('hud-number'), tag: $('hud-tag'), label: $('hud-label'), sub: $('hud-sub'), progress: $('hud-progress') },
  net: $('net'), netStep: $('net-step'), matrixLog: $('matrix-log'), matrixToggle: $('matrix-toggle'),
  sizePicker: $('size-picker'), widthPicker: $('width-picker'),
  speed: $('speed'), speedRange: $('speed-range'),
  composeToggle: $('compose-toggle'), composer: $('composer'), pending: $('pending'),
  applyStep: $('apply-step'), clearPending: $('clear-pending'),
  solve: $('solve'), scramble: $('scramble'), reset: $('reset'), pause: $('pause'),
  history: $('history'), historyCount: $('history-count'), toast: $('toast'),
};

const scene = new CubeScene(ui.rig, ui.cube);
const net = new NetView(ui.net);
const state = { size: DEFAULT_SIZE, width: 1, composing: false, pending: [], paused: false, resume: null, toastTimer: 0 };

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// ---------- speed ----------

const clampSpeed = (value) => Math.min(MAX_SPEED, Math.max(MIN_SPEED, Number(value) || MIN_SPEED));
const quarterTurnMs = () => (QUARTER_TURN_DEGREES / clampSpeed(ui.speed.value)) * 1000;

ui.speedRange.addEventListener('input', () => { ui.speed.value = ui.speedRange.value; });
ui.speed.addEventListener('change', () => {
  ui.speed.value = clampSpeed(ui.speed.value);
  ui.speedRange.value = ui.speed.value;
});

// ---------- hud, history, matrix log ----------

function showIdle() {
  ui.hud.number.textContent = 'Gata';
  ui.hud.tag.hidden = true;
  ui.hud.label.textContent = 'Apasă o săgeată de pe cub ca să rotești un strat.';
  ui.hud.sub.textContent = '';
  ui.hud.progress.style.width = '0';
}

function showStepStart(record) {
  const tag = originTag(record.origin);
  ui.hud.number.textContent = `Pasul ${record.number}`;
  ui.hud.tag.textContent = tag;
  ui.hud.tag.hidden = !tag;
  ui.hud.label.textContent = describeStep(record.moves);
  ui.netStep.textContent = `Pasul ${record.number}`;
}

function showTurnProgress(index, total) {
  ui.hud.sub.textContent = `Rotirea ${index} din ${total}`;
  ui.hud.progress.style.width = `${(index / total) * 100}%`;
}

const formatCell = ([face, row, col]) => `${FACE_NAMES[face]}[${row + 1}][${col + 1}]`;

function showMatrixLog({ description, transfers }) {
  const lines = transfers.slice(0, MAX_LOGGED_TRANSFERS).map(([from, to]) => `<li>${formatCell(from)} → ${formatCell(to)}</li>`);
  const hidden = transfers.length - MAX_LOGGED_TRANSFERS;
  if (hidden > 0) lines.push(`<li>… încă ${hidden} mutări de căsuțe</li>`);
  ui.matrixLog.innerHTML = `<p class="desc">${description}</p><ul>${lines.join('')}</ul>`;
}

function addHistory(record) {
  for (const item of ui.history.querySelectorAll('.current')) item.classList.remove('current');
  const item = document.createElement('li');
  item.className = 'current';
  item.innerHTML = `<span class="num"></span><span class="label"></span><span class="tag"></span>`;
  item.children[0].textContent = record.number;
  item.children[1].textContent = describeStep(record.moves);
  item.children[2].textContent = originTag(record.origin);
  ui.history.append(item);
  item.scrollIntoView({ block: 'nearest' });
  ui.historyCount.textContent = ui.history.children.length;
}

// ---------- playback ----------

function setBusy(isBusy) {
  document.body.dataset.busy = String(isBusy);
  for (const element of document.querySelectorAll('[data-lock]')) element.disabled = isBusy;
  for (const button of ui.sizePicker.children) button.disabled = isBusy;
  ui.clearPending.disabled = isBusy || state.pending.length === 0;
  ui.applyStep.disabled = isBusy || state.pending.length === 0;
}

const untilResumed = () => (state.paused ? new Promise((resolve) => { state.resume = resolve; }) : Promise.resolve());

async function playTurn(frame, index, total) {
  await untilResumed();
  showTurnProgress(index, total);
  showMatrixLog(frame);
  const duration = quarterTurnMs();
  await Promise.all([
    scene.turn(frame.direction, frame.layers, duration, frame.faces),
    net.slide(frame.transfers, duration, frame.faces),
  ]);
}

async function playSteps(steps) {
  for (const { record, frames } of steps) {
    showStepStart(record);
    for (const [index, frame] of frames.entries()) await playTurn(frame, index + 1, frames.length);
    addHistory(record);
    await sleep(STEP_PAUSE_MS);
  }
}

async function perform(request) {
  setBusy(true);
  try {
    const { steps, state: finalState } = await request();
    await playSteps(steps);
    scene.paint(finalState.faces);
    net.setFaces(finalState.faces);
    return steps.length;
  } catch (error) {
    showToast(error.message);
    return 0;
  } finally {
    setBusy(false);
  }
}

function showToast(message) {
  ui.toast.textContent = message;
  ui.toast.hidden = false;
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => { ui.toast.hidden = true; }, TOAST_MS);
}

// ---------- cube state ----------

function layersFor(index) {
  const first = Math.min(index, state.size - state.width);
  return Array.from({ length: state.width }, (_, offset) => first + offset);
}

function loadState(serverState) {
  state.size = serverState.size;
  state.pending = [];
  renderPending();
  scene.build(serverState.size, serverState.stickers);
  scene.paint(serverState.faces);
  net.build(serverState.size);
  net.setFaces(serverState.faces);
  buildHandles(ui.handles, serverState.size, {
    onPress: handlePress,
    onHover: (direction, index) => scene.highlight(direction, layersFor(index)),
    onLeave: () => scene.clearHighlight(),
  });
  ui.history.replaceChildren();
  serverState.history.forEach(addHistory);
  ui.historyCount.textContent = serverState.history.length;
  ui.netStep.textContent = 'Stare inițială';
  ui.matrixLog.innerHTML = '';
  for (const button of ui.sizePicker.children) button.setAttribute('aria-checked', String(Number(button.dataset.size) === serverState.size));
  showIdle();
}

// ---------- moves and composed steps ----------

function handlePress(direction, index) {
  scene.clearHighlight();
  const [layer] = layersFor(index);
  const move = { direction, layer, width: state.width, times: 1 };
  if (state.composing) addPending(move);
  else perform(() => api.step([move]));
}

function addPending(move) {
  const last = state.pending.at(-1);
  const repeatsLast = last && last.direction === move.direction && last.layer === move.layer && last.width === move.width;
  if (repeatsLast) last.times = Math.min(MAX_TIMES, last.times + 1);
  else state.pending.push(move);
  renderPending();
}

function renderPending() {
  const chips = state.pending.map((move, index) => {
    const chip = document.createElement('li');
    const label = document.createElement('span');
    label.textContent = describeMove(move);
    const remove = document.createElement('button');
    remove.type = 'button';
    remove.textContent = '×';
    remove.setAttribute('aria-label', `Elimină ${describeMove(move)}`);
    remove.addEventListener('click', () => { state.pending.splice(index, 1); renderPending(); });
    chip.append(label, remove);
    return chip;
  });
  ui.pending.replaceChildren(...chips);
  const isBusy = document.body.dataset.busy === 'true';
  ui.applyStep.disabled = isBusy || chips.length === 0;
  ui.clearPending.disabled = isBusy || chips.length === 0;
}

function setSelected(group, selectedButton) {
  for (const button of group.children) button.setAttribute('aria-checked', String(button === selectedButton));
}

// ---------- wiring ----------

ui.sizePicker.replaceChildren(...SIZES.map((size) => {
  const button = document.createElement('button');
  button.type = 'button';
  button.role = 'radio';
  button.dataset.size = size;
  button.textContent = size;
  button.setAttribute('aria-checked', String(size === DEFAULT_SIZE));
  button.addEventListener('click', async () => {
    if (size === state.size) return;
    const { state: fresh } = await api.reset(size);
    loadState(fresh);
  });
  return button;
}));

ui.widthPicker.addEventListener('click', (event) => {
  const button = event.target.closest('button');
  if (!button) return;
  state.width = Number(button.dataset.width);
  setSelected(ui.widthPicker, button);
});

ui.composeToggle.addEventListener('click', () => {
  state.composing = !state.composing;
  ui.composeToggle.setAttribute('aria-checked', String(state.composing));
  ui.composer.hidden = !state.composing;
  if (!state.composing) { state.pending = []; renderPending(); }
});

ui.applyStep.addEventListener('click', async () => {
  const moves = state.pending;
  state.pending = [];
  renderPending();
  await perform(() => api.step(moves));
});
ui.clearPending.addEventListener('click', () => { state.pending = []; renderPending(); });

ui.matrixToggle.addEventListener('click', () => {
  const isOn = ui.matrixToggle.getAttribute('aria-pressed') !== 'true';
  ui.matrixToggle.setAttribute('aria-pressed', String(isOn));
  net.setDetailed(isOn);
  ui.matrixLog.hidden = !isOn;
});

ui.solve.addEventListener('click', async () => {
  const count = await perform(() => api.solve());
  if (count === 0) showToast('Cubul este deja rezolvat.');
});
ui.scramble.addEventListener('click', () => perform(() => api.scramble(SCRAMBLE_STEPS)));
ui.reset.addEventListener('click', async () => loadState((await api.reset(state.size)).state));

ui.pause.addEventListener('click', () => {
  state.paused = !state.paused;
  ui.pause.setAttribute('aria-pressed', String(state.paused));
  ui.pause.textContent = state.paused ? 'Continuă' : 'Pauză';
  if (!state.paused && state.resume) { state.resume(); state.resume = null; }
});

enableOrbit(ui.viewport, ui.rig);
loadState((await api.state()));
