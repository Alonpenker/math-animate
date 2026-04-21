import type { ReactNode } from "react";

export function SectionText({ children }: { children: ReactNode }) {
    return (
       <p className="mt-3 text-off-white/60 leading-relaxed max-w-2xl">
            {children}
        </p> 
    )
}

interface InfoSectionProps {
  title: string;
  children: ReactNode;
}


export function InfoSection({title, children}: InfoSectionProps) {
    
    return (
        <section>
            <h2 className="text-4xl font-semibold text-off-white">{title}</h2>
            {children}
        </section>
        );
}