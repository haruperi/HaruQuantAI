import { afterEach, expect, test, vi } from 'vitest';

const mount = vi.hoisted(() => ({ render: vi.fn(), createRoot: vi.fn() }));
vi.mock('react-dom/client', () => ({ createRoot: mount.createRoot }));
vi.mock('../shell/App', () => ({ App: () => null }));

afterEach(() => {
  vi.unstubAllGlobals();
  vi.resetModules();
  vi.clearAllMocks();
});

test('entrypoint remains safe without a browser document', async () => {
  await import('../shell/bootstrap');
  expect(mount.createRoot).not.toHaveBeenCalled();
});

test('entrypoint mounts the application into the existing root', async () => {
  const root = { id: 'root' };
  mount.createRoot.mockReturnValue({ render: mount.render });
  vi.stubGlobal('document', { getElementById: (id: string) => id === 'root' ? root : null });
  await import('../shell/bootstrap');
  expect(mount.createRoot).toHaveBeenCalledWith(root);
  expect(mount.render).toHaveBeenCalledOnce();
});

test('entrypoint does not create a root when the host element is absent', async () => {
  vi.stubGlobal('document', { getElementById: () => null });
  await import('../shell/bootstrap');
  expect(mount.createRoot).not.toHaveBeenCalled();
});
