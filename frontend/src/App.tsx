import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Home } from './pages/Home';
import { CreateNewsletter } from './pages/CreateNewsletter';
import { ReviewNewsletter } from './pages/ReviewNewsletter';
import { PublishNewsletter } from './pages/PublishNewsletter';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/create" element={<CreateNewsletter />} />
        <Route path="/review" element={<ReviewNewsletter />} />
        <Route path="/publish" element={<PublishNewsletter />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
