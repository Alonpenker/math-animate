import { Component } from 'react';
import type { ReactNode, ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center p-4 text-center">
          <div>
            <h1 className="text-2xl font-bold text-off-white">Something went wrong.</h1>
            <p className="mt-2 text-off-white/50">Refresh the page to try again.</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 rounded-md bg-accent-orange px-4 py-2 text-surface-dark hover:bg-accent-orange/80"
            >
              Refresh
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
