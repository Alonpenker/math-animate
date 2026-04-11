import type { ReactNode } from 'react';
import LogoLoop from '@/components/ui/LogoLoop';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip';
import {
  SiFastapi, SiPostgresql, SiRedis, SiReact,
  SiCloudflare, SiRabbitmq, SiOpenai, SiPython,
  SiTypescript, SiLangchain, SiDocker, SiAnthropic,
  SiVite, SiTailwindcss, SiOllama, SiTerraform,
  SiGithub, SiCelery, SiMinio,
} from 'react-icons/si';
import { FaAws } from 'react-icons/fa';

type LogoItem = { node: ReactNode; title: string };

function icon(Icon: React.ElementType, label: string): LogoItem {
  return {
    node: (
      <Tooltip>
        <TooltipTrigger render={<span style={{ display: 'inline-flex', cursor: 'default' }} />}>
          <Icon
            style={{
              fontSize: 48,
              color: 'rgba(245,240,232,0.35)',
              filter: 'grayscale(1)',
              display: 'block',
            }}
          />
        </TooltipTrigger>
        <TooltipContent>{label}</TooltipContent>
      </Tooltip>
    ),
    title: label,
  };
}

const LOGOS: LogoItem[] = [
  icon(SiFastapi,    'FastAPI'),
  icon(SiLangchain,  'LangChain'),
  icon(SiPostgresql, 'PostgreSQL'),
  icon(SiRedis,      'Redis'),
  icon(SiReact,      'React'),
  icon(FaAws,        'AWS'),
  icon(SiCloudflare, 'Cloudflare'),
  icon(SiRabbitmq,   'RabbitMQ'),
  icon(SiOpenai,     'OpenAI'),
  icon(SiPython,     'Python'),
  icon(SiTypescript, 'TypeScript'),
  icon(SiDocker,     'Docker'),
  icon(SiAnthropic,  'Claude Code'),
  icon(SiVite,       'Vite'),
  icon(SiTailwindcss,'Tailwind CSS'),
  icon(SiOllama,     'Ollama'),
  icon(SiTerraform,  'Terraform'),
  icon(SiGithub,     'GitHub'),
  icon(SiCelery,     'Celery'),
  icon(SiMinio,      'MinIO'),
];

export function TechLoopStrip() {
  return (
    <div className="py-8 border-y border-off-white/10">
      <p className="text-center text-xs text-off-white/30 mb-6">Built with</p>
      <TooltipProvider delay={200}>
        <LogoLoop
          logos={LOGOS}
          speed={60}
          direction="left"
          logoHeight={48}
          gap={56}
          pauseOnHover
          scaleOnHover={true}
          fadeOut
          fadeOutColor="#000000"
          ariaLabel="Technologies used"
        />
      </TooltipProvider>
    </div>
  );
}
