import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';
import { HomePage } from '@/pages/HomePage';
import { CreatePage } from '@/pages/CreatePage';
import { JobsPage } from '@/pages/JobsPage';
import { LessonsPage } from '@/pages/LessonsPage';
import { UsagePage } from '@/pages/UsagePage';
import { ErrorBoundary } from '@/components/ErrorBoundary';

export default function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <div className="flex min-h-screen flex-col">
          <Navbar />
          <main className="flex-1 pt-14">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/create" element={<CreatePage />} />
              <Route path="/jobs" element={<JobsPage />} />
              <Route path="/lessons" element={<LessonsPage />} />
              <Route path="/usage" element={<UsagePage />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </ErrorBoundary>
    </BrowserRouter>
  );
}
