export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export function formatNumber(n: number): string {
  return n.toLocaleString('en-US');
}

export function truncateId(id: string): string {
  return id.length > 8 ? `${id.slice(0, 8)}...` : id;
}
