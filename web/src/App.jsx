import { Routes, Route, useLocation } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import ScrollToTop from './components/ScrollToTop'
import Home from './pages/Home'
import Destinations from './pages/Destinations'
import DestinationDetail from './pages/DestinationDetail'

export default function App() {
  const location = useLocation()
  return (
    <div className="flex min-h-screen flex-col">
      <ScrollToTop />
      <Navbar />
      <main className="flex-1">
        {/* La cle force un remontage a chaque route -> animation d'entree */}
        <div key={location.pathname} className="animate-pagefade">
          <Routes location={location}>
            <Route path="/" element={<Home />} />
            <Route path="/destinations" element={<Destinations />} />
            <Route path="/destinations/:nom" element={<DestinationDetail />} />
          </Routes>
        </div>
      </main>
      <Footer />
    </div>
  )
}
