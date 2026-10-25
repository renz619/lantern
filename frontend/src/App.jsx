import { useState } from 'react'
import BottomNav from './components/BottomNav'
import ScanPage from './pages/ScanPage'
import SearchPage from './pages/SearchPage'
import HistoryPage from './pages/HistoryPage'

function App() {
  const [tab, setTab] = useState('scan')

  return (
    <>
      <header className="title-bar">
        <div className="title-bar-inner">Lantern</div>
      </header>
      <main className="app">
        {tab === 'scan' && <ScanPage goTo={setTab} />}
        {tab === 'search' && <SearchPage goTo={setTab} />}
        {tab === 'history' && <HistoryPage goTo={setTab} />}
      </main>
      <BottomNav tab={tab} setTab={setTab} />
    </>
  )
}

export default App
