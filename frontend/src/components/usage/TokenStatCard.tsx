interface TokenStatCardProps {
  title: string;
  value: string;
  subtitle: string;
  children?: React.ReactNode;
}

export function TokenStatCard({ title, value, subtitle, children }: TokenStatCardProps) {
  return (
    <div className="rounded-lg border border-brand-border p-6">
      <p className="text-sm font-medium text-brand-muted">{title}</p>
      <p className="mt-2 text-3xl font-bold text-brand-text">{value}</p>
      <p className="mt-1 text-sm text-brand-muted">{subtitle}</p>
      {children}
    </div>
  );
}
