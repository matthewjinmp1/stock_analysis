import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './components/ThemeContext';
import Layout from './components/Layout';

import SearchPage from './pages/SearchPage';
import WatchlistPage from './pages/WatchlistPage';
import AIScoresPage from './pages/AIScoresPage';
import PeersPage from './pages/PeersPage';
import MetricsPage from './pages/MetricsPage';
import FinancialsPage from './pages/FinancialsPage';
import AdjustedPEPage from './pages/AdjustedPEPage';
import FindPeersPage from './pages/FindPeersPage';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Layout maxWidth="800px"><SearchPage /></Layout>} />
          <Route path="/watchlist" element={<Layout maxWidth="1200px"><WatchlistPage /></Layout>} />
          <Route path="/ai-scores" element={<Layout maxWidth="1400px"><AIScoresPage /></Layout>} />
          <Route path="/peers/:ticker" element={<Layout maxWidth="1400px"><PeersPage /></Layout>} />
          <Route path="/metrics/:ticker" element={<Layout maxWidth="1200px"><MetricsPage /></Layout>} />
          <Route path="/financial/:ticker" element={<Layout maxWidth="1200px"><FinancialsPage /></Layout>} />
          <Route path="/adjusted-pe/:ticker" element={<Layout maxWidth="1000px"><AdjustedPEPage /></Layout>} />
          <Route path="/find-peers" element={<Layout maxWidth="800px"><FindPeersPage /></Layout>} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
