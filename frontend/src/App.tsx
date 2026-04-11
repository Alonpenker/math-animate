import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { GlassNavbar } from '@/components/layout/GlassNavbar';
import { Footer } from '@/components/layout/Footer';
import { HomePage } from '@/pages/HomePage';
import { CreatePage } from '@/pages/CreatePage';
import { JobsPage } from '@/pages/JobsPage';
import { LessonsPage } from '@/pages/LessonsPage';
import { UsagePage } from '@/pages/UsagePage';
import { AboutPage } from '@/pages/AboutPage';
import { ErrorBoundary } from '@/components/ErrorBoundary';

export default function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <div className="flex min-h-screen flex-col">
          <GlassNavbar />
          <main className="flex-1 pt-20">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/create" element={<CreatePage />} />
              <Route path="/jobs" element={<JobsPage />} />
              <Route path="/lessons" element={<LessonsPage />} />
              <Route path="/usage" element={<UsagePage />} />
              <Route path="/about" element={<AboutPage />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </ErrorBoundary>
    </BrowserRouter>
  );
}
