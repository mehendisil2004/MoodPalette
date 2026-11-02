import { useState, useEffect } from 'react'
import { Chart as C, ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'
import { Doughnut, Bar } from 'react-chartjs-2'
C.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

const API_BASE = "https://moodpalette-il8f.onrender.com";

const api = (p, method = "GET", body) =>
  fetch(`${API_BASE}/api${p}`, {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.status === 204 ? null : response.json();
  });

const Q = [
  ['introversion', 'Your ideal Saturday?', [['🛋️', 'Cosy night in, just me', .9], ['☕', 'Brunch with a few friends', .5], ['🎉', 'A big, buzzy party', .1]]],
  ['creativity', 'You find a blank notebook…', [['🎨', 'Sketch, doodle, invent!', .9], ['📝', 'Make neat lists', .4], ['📦', "Keep it for later", .1]]],
  ['adventurousness', 'A surprise trip appears!', [['✈️', 'Pack now, figure it out later', .9], ['🗺️', 'Plan it carefully', .5], ['🏡', "I'd rather stay home", .1]]],
  ['calmness', 'Plans suddenly change…', [['🌿', 'Breathe, go with it', .9], ['😅', 'Slightly flustered', .5], ['🌪️', 'Total chaos inside', .1]]],
  ['romanticism', 'Your love language is…', [['💌', 'Love letters & candlelight', .9], ['🌸', 'Little thoughtful gestures', .55], ['🧩', 'Practical, helpful acts', .15]]]]
const MOODS = { happy: '🌼', dreamy: '☁️', calm: '🍃', romantic: '🌹', energetic: '⚡', melancholic: '🌧️', mysterious: '🌙' }

export default function App() {
  const [view, setView] = useState('home'), [qi, setQi] = useState(0), [ans, setAns] = useState({})
  const [pal, setPal] = useState(null), [busy, setBusy] = useState(false), [toast, setToast] = useState('')
  const [list, setList] = useState([]), [favOnly, setFav] = useState(false)
  const load = () => api('/palettes').then(setList)
  useEffect(() => { if (view === 'dash') load() }, [view])
  const say = m => { setToast(m); setTimeout(() => setToast(''), 1500) }
  const copy = h => { navigator.clipboard?.writeText(h); say(`Copied ${h} 💗`) }

  const generate = async (mood) => {
    try {
      setBusy(true);

      console.log("Sending generation request:", {
        url: `${API_BASE}/api/generate`,
        traits: ans,
        mood,
      });

      const result = await api("/generate", "POST", {
        traits: ans,
        mood,
      });

      console.log("Generated palette:", result);

      setPal(result);
      setView("result");
    } catch (error) {
      console.error("Palette generation failed:", error);
      alert("Palette generation failed: " + error.message);
    } finally {
      setBusy(false);
    }
  };
  const swap = async i => {
    const r = await api('/replace', 'POST', { hexes: pal.colors.map(c => c.hex), index: i, traits: pal.traits, mood: pal.mood })
    const colors = pal.colors.map((c, k) => (k === i ? { ...c, ...r, role: c.role } : c))
    setPal(await api('/palettes/' + pal.id, 'PATCH', { colors }))
  }
  const fav = async p => { const u = await api('/palettes/' + p.id, 'PATCH', { favourite: !p.favourite }); if (p.id === pal?.id) setPal(u); load() }
  const Strip = ({ p }) => <div className="flex h-12 rounded-2xl overflow-hidden">{p.colors.map(c => <div key={c.hex} style={{ background: c.hex }} className="flex-1" />)}</div>

  const moodCounts = list.reduce((a, p) => ({ ...a, [p.mood]: (a[p.mood] || 0) + 1 }), {})
  const perDay = list.reduce((a, p) => { const d = p.created_at.slice(0, 10); a[d] = (a[d] || 0) + 1; return a }, {})

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <header className="flex justify-between items-center mb-8">
        <h1 onClick={() => setView('home')} className="font-serif italic text-3xl cursor-pointer">MoodPalette 🎀</h1>
        <button className="btn bg-white/70" onClick={() => setView('dash')}>My Collection</button>
      </header>
      {toast && <div className="fixed top-4 left-1/2 -translate-x-1/2 card px-5 py-2 animate-pop z-10">{toast}</div>}

      {view === 'home' && <div className="card p-10 text-center animate-pop">
        <div className="text-6xl mb-3">🌸</div>
        <h2 className="font-serif text-4xl mb-3">Colours that feel like <i>you</i></h2>
        <p className="mb-6 max-w-md mx-auto">Take a 5-question personality quiz, pick today's mood, and let our ML engine compose your palette.</p>
        <button className="btn bg-rose text-white shadow-soft" onClick={() => { setAns({}); setQi(0); setView('quiz') }}>Start the quiz ✨</button>
      </div>}

      {view === 'quiz' && <div className="card p-8 animate-pop" key={qi}>
        <div className="h-2 rounded-full bg-lav/40 mb-6"><div className="h-2 rounded-full bg-rose transition-all" style={{ width: `${(qi / Q.length) * 100}%` }} /></div>
        <h2 className="font-serif text-2xl mb-5">{Q[qi][1]}</h2>
        <div className="grid sm:grid-cols-3 gap-4">
          {Q[qi][2].map(([e, t, v]) => <button key={t} className="rounded-3xl bg-cream p-5 shadow-soft hover:-translate-y-1 hover:bg-blush transition"
            onClick={() => { setAns({ ...ans, [Q[qi][0]]: v }); qi + 1 < Q.length ? setQi(qi + 1) : setView('mood') }}>
            <div className="text-4xl mb-2">{e}</div>{t}</button>)}
        </div></div>}

      {view === 'mood' && <div className="card p-8 text-center animate-pop">
        <h2 className="font-serif text-2xl mb-5">How are you feeling right now?</h2>
        <div className="flex flex-wrap justify-center gap-4">
          {Object.entries(MOODS).map(([m, e]) => <button key={m} disabled={busy} onClick={() => generate(m)}
            className="rounded-full bg-cream shadow-soft px-6 py-4 hover:bg-lav/60 hover:scale-105 transition capitalize"><span className="text-2xl mr-2">{e}</span>{m}</button>)}
        </div></div>}

      {view === 'result' && pal && <div>
        <div className="text-center mb-6 animate-pop">
          <p className="text-sm uppercase tracking-widest">{pal.archetype} · {pal.mood} · {pal.scheme}</p>
          <h2 className="font-serif italic text-4xl my-2">{pal.name}</h2>
          <div className="flex justify-center gap-3 mt-4">
            <button className="btn bg-rose text-white" onClick={() => generate(pal.mood)}>Regenerate 🔄</button>
            <button className="btn bg-white/80" onClick={() => fav(pal)}>{pal.favourite ? '💖 Saved' : '🤍 Save'}</button>
            <button className="btn bg-white/80" onClick={() => setView('mood')}>Change mood</button>
          </div>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {pal.colors.map((c, i) => <div key={c.hex + i} style={{ animationDelay: `${i * 70}ms` }} className="card overflow-hidden animate-pop">
            <button onClick={() => copy(c.hex)} style={{ background: c.hex }} className="h-32 w-full" title="Copy HEX" />
            <div className="p-4"><div className="flex justify-between items-center">
              <b>{c.name}</b><code onClick={() => copy(c.hex)} className="cursor-pointer bg-blush/60 rounded-full px-2 text-sm">{c.hex}</code></div>
              <p className="text-sm mt-2">{c.why}</p>
              <button className="text-xs mt-3 underline" onClick={() => swap(i)}>↻ replace this colour</button></div>
          </div>)}
        </div></div>}

      {view === 'dash' && <div className="space-y-6 animate-pop">
        <div className="grid md:grid-cols-2 gap-5">
          <div className="card p-5"><h3 className="font-serif text-xl mb-2">Mood history</h3>
            {list.length ? <Doughnut data={{ labels: Object.keys(moodCounts), datasets: [{ data: Object.values(moodCounts), backgroundColor: ['#fbd5e0', '#d9c8f2', '#e58fb0', '#ffe9c7', '#b9d7ea', '#c9b6e4', '#f4a6c0'] }] }} /> : <p>No palettes yet 🌷</p>}</div>
          <div className="card p-5"><h3 className="font-serif text-xl mb-2">Palettes per day</h3>
            <Bar data={{ labels: Object.keys(perDay), datasets: [{ label: 'Palettes', data: Object.values(perDay), backgroundColor: '#e58fb0', borderRadius: 8 }] }} /></div>
        </div>
        <div className="flex gap-3"><button className={`btn ${!favOnly ? 'bg-rose text-white' : 'bg-white/70'}`} onClick={() => setFav(false)}>All</button>
          <button className={`btn ${favOnly ? 'bg-rose text-white' : 'bg-white/70'}`} onClick={() => setFav(true)}>💖 Favourites</button></div>
        <div className="grid sm:grid-cols-2 gap-5">
          {list.filter(p => !favOnly || p.favourite).map(p => <div key={p.id} className="card p-4">
            <Strip p={p} />
            <div className="flex justify-between items-center mt-3"><div><b className="font-serif">{p.name}</b>
              <div className="text-xs">{MOODS[p.mood]} {p.mood} · {p.created_at.slice(0, 10)}</div></div>
              <div className="flex gap-2"><button onClick={() => { setPal(p); setView('result') }}>👁️</button>
                <button onClick={() => fav(p)}>{p.favourite ? '💖' : '🤍'}</button>
                <button onClick={async () => { await api('/palettes/' + p.id, 'DELETE'); load() }}>🗑️</button></div></div>
            <div className="flex flex-wrap gap-1 mt-2">{p.colors.map(c => <code key={c.hex} onClick={() => copy(c.hex)} className="cursor-pointer text-xs bg-blush/50 rounded-full px-2">{c.hex}</code>)}</div>
          </div>)}
        </div></div>}
    </div>)
}