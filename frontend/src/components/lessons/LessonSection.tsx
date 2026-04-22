import { useState } from 'react';
import type { Dispatch, SetStateAction } from 'react'
import { useNavigate } from 'react-router-dom';

import { BookOpen } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { LessonCard } from '@/components/lessons/LessonCard';
import { LessonDialog } from '@/components/lessons/LessonDialog';
import type { JobListItem } from '@/services/api';

interface LessonSectionProps{
    lessons: JobListItem[]
    isLoading: boolean
    error: Error | null
    page: number
    totalPages: number
    onSetPage: Dispatch<SetStateAction<number>>
}


export function LessonSection({ lessons, isLoading, error, page, totalPages, onSetPage }: LessonSectionProps) {
    const navigate = useNavigate();
    const [selectedJob, setSelectedJob] = useState<JobListItem | null>(null);
    let content;
    
    if (error) {
        content = (<div className="flex flex-col items-center py-16 text-center">
            <p className="text-off-white/50">Could not load lessons.</p>
            <Button variant="outline" className="mt-4" onClick={() => window.location.reload()}>Retry</Button>
          </div>)
    }
          
    if (isLoading && !error) {
        content =  (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-36 rounded-lg" style={{ background: 'rgba(245,240,232,0.08)' }} />
            ))}
          </div>
        )
    }
    
    if (!isLoading && !error && lessons.length === 0) {
        content = (
            <div className="flex flex-col items-center py-16 text-center">
            <BookOpen className="h-12 w-12 text-off-white/30" />
            <p className="mt-4 text-off-white/50">No rendered videos yet. Create your first lesson!</p>
            <Button className="mt-4 bg-accent-orange hover:bg-accent-orange/80" onClick={() => navigate('/create')}>
              Create a Lesson
            </Button>
          </div>
        )
    }
    
    
    if (!isLoading && !error && lessons.length > 0) {
        content = (
            <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {lessons.map((lesson) => (
                <LessonCard key={lesson.job_id} job={lesson} onClick={() => setSelectedJob(lesson)} />
              ))}
            </div>
            {totalPages > 1 && (
              <div className="mt-8 flex items-center justify-center gap-5">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onSetPage(p => p - 1)}>Previous</Button>
                <span className="text-sm text-off-white/50">Page {page} of {totalPages}</span>
                <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => onSetPage(p => p + 1)}>Next</Button>
              </div>
            )}
          </>
        )
    }
      
    return (
        <>
            {content}
            {selectedJob && (
                <LessonDialog
                key={selectedJob.job_id}
                onClose={() => setSelectedJob(null)}
                jobId={selectedJob.job_id}
                topic={selectedJob.topic}
                />
            )}
        </>
        );
}
