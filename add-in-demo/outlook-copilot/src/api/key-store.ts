export type Provider = "anthropic" | "deepseek";

const LS_PROVIDER = "hk_provider";
const LS_KEY_PREFIX = "hk_api_key_";

export function getProvider(): Provider {
  return (localStorage.getItem(LS_PROVIDER) as Provider) || "anthropic";
}

export function setProvider(p: Provider): void {
  localStorage.setItem(LS_PROVIDER, p);
}

export function getApiKey(provider?: Provider): string {
  const p = provider ?? getProvider();
  const stored = localStorage.getItem(`${LS_KEY_PREFIX}${p}`);
  if (stored) return stored;
  // Fallback to env var for Anthropic (dev convenience)
  if (p === "anthropic") return (import.meta.env.VITE_ANTHROPIC_API_KEY as string) || "";
  return "";
}

export function setApiKey(key: string, provider?: Provider): void {
  localStorage.setItem(`${LS_KEY_PREFIX}${provider ?? getProvider()}`, key);
}

export function clearApiKey(provider?: Provider): void {
  localStorage.removeItem(`${LS_KEY_PREFIX}${provider ?? getProvider()}`);
}

export function hasKey(provider?: Provider): boolean {
  return !!getApiKey(provider);
}
