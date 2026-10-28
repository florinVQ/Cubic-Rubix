async function request(path, body) {
  const options = body === undefined ? {} : {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  };
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error ?? response.statusText);
  return data;
}

export const api = {
  state: () => request('/api/state'),
  reset: (size) => request('/api/reset', { size }),
  step: (moves) => request('/api/step', { moves }),
  scramble: (count) => request('/api/scramble', { count }),
  solve: () => request('/api/solve', {}),
};
