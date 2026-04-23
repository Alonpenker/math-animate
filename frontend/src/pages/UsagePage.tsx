import { motion } from 'framer-motion';
import { UsageSection } from '@/components/usage/UsageSection';
import { useQuery } from '@tanstack/react-query';
import { getTokenUsage } from '@/services/api';

export function UsagePage() {
  const { data, isLoading, error, refetch } = useQuery({
        queryKey: ['usage'],
        queryFn: getTokenUsage,
      });
 

  return (
    <div className="px-4 py-12">
      <motion.div
        className="mx-auto max-w-4xl"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="mb-8">
          <h1 className="text-4xl text-off-white">
            Token Usage
          </h1>
          <p className="mt-2 text-off-white/50 max-w-xl">
            MathAnimate is free to use. To keep costs sustainable, there is a shared daily limit of 250,000 tokens. This resets at midnight UTC.
          </p>
        </div>
        <UsageSection isLoading={isLoading} error={error} data={data} onClick={refetch}/>
      </motion.div>
    </div>
  );
}
