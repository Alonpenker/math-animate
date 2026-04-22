import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search } from 'lucide-react';
import { motion } from 'framer-motion';
import { Input } from '@/components/ui/input';
import { useLessons } from '@/hooks/useLessons';
import { LessonSection } from '@/components/lessons/LessonSection';

export function LessonsPage() {
  
  const [searchParams] = useSearchParams();
  const jobIdFilter = searchParams.get('job_id') ?? undefined;
  const [topicQuery, setTopicQuery] = useState('');
  const [page, setPage] = useState(1);
  
  const { lessons, totalPages, isLoading, error } = useLessons({ topicQuery, jobId: jobIdFilter, page });

  return (
    <div className="px-4 py-12">
      <motion.div
        className="mx-auto max-w-5xl"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="mb-8">
          <h1 className="text-4xl text-off-white">
            Lesson Library
          </h1>
          <p className="mt-2 text-off-white/50">
            Browse and watch your rendered lesson videos.
          </p>
        </div>

        <div className="relative mb-8">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-off-white/40" />
          <Input
            type="text"
            value={topicQuery}
            onChange={(e) => { setTopicQuery(e.target.value); setPage(1); }}
            placeholder="Search by topic..."
            className="pl-10"
          />
        </div>
        
        <LessonSection lessons={lessons} isLoading={isLoading} error={error} page={page} totalPages={totalPages} onSetPage={setPage}/>
        </motion.div>
    </div>
  );
}
