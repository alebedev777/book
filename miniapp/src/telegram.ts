export function getInitData(): string {
  const tg = window.Telegram?.WebApp;
  if (tg?.initData) return tg.initData;
  return import.meta.env.VITE_DEV_INIT_DATA || "";
}

export function ready(): void {
  window.Telegram?.WebApp?.ready();
  window.Telegram?.WebApp?.expand();
}