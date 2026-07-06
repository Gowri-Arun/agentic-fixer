export async function copyToClipboard(value: string): Promise<void> {
  await navigator.clipboard.writeText(value);
}
