import type { ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";

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
    const shouldReduce = useReducedMotion();

    return (
        <motion.section
          initial={shouldReduce ? false : { opacity: 0, y: 24 }}
          whileInView={shouldReduce ? undefined : { opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
            <h2 className="text-4xl font-semibold text-off-white">{title}</h2>
            {children}
        </motion.section>
        );
}