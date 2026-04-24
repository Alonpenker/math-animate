import type { ReactNode } from 'react';

import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';
import {
  SiFastapi, SiPostgresql, SiRedis, SiReact,
  SiCloudflare, SiRabbitmq, SiOpenai, SiPython,
  SiTypescript, SiLangchain, SiDocker, SiAnthropic,
  SiVite, SiTailwindcss, SiOllama, SiTerraform,
  SiGithub, SiCelery, SiMinio,
} from 'react-icons/si';
import { FaAws } from 'react-icons/fa';

type LogoIconProps = {
  Icon: React.ElementType
  label: string
}

function LogoIcon({ Icon, label }: LogoIconProps): React.ReactElement {
    return (
        <Tooltip>
            <TooltipTrigger delay={0} render={<span style={{ display: 'inline-flex', cursor: 'default' }} />}>
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
    );
}

function icon(Icon: React.ElementType, label: string): LogoItem {
  return {
        node: <LogoIcon Icon={Icon} label={label} />,
        title: label,
  };
}


type LogoItem = { node: ReactNode; title: string };

export const LOGOS: LogoItem[] = [
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