import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';

export function useLessonsSearch() {
  const [searchParams, setSearchParams] = useSearchParams();
  const jobIdFilter = searchParams.get('job_id') ?? undefined;
  const [topicQuery, setTopicQuery] = useState('');
  const [page, setPage] = useState(1);

  function handleTopicChange(nextTopicQuery: string) {
    if (jobIdFilter && nextTopicQuery.trim() !== '') {
      const nextSearchParams = new URLSearchParams(searchParams);
      nextSearchParams.delete('job_id');
      setSearchParams(nextSearchParams, { replace: true });
    }

    setTopicQuery(nextTopicQuery);
    setPage(1);
  }

  return {
    jobIdFilter,
    topicQuery,
    page,
    setPage,
    handleTopicChange,
  };
}
