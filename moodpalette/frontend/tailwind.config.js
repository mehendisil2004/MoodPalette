export default { content: ['./index.html', './src/**/*.{jsx,js}'],
  theme: { extend: {
    colors: { blush: '#fbd5e0', rose: '#e58fb0', lav: '#d9c8f2', plum: '#7a5a8a', cream: '#fff8f0' },
    fontFamily: { serif: ['"Playfair Display"', 'serif'], sans: ['Quicksand', 'sans-serif'] },
    boxShadow: { soft: '0 10px 30px -10px rgba(190,120,160,.35)' },
    keyframes: { pop: { '0%': { opacity: 0, transform: 'scale(.9) translateY(10px)' }, '100%': { opacity: 1, transform: 'none' } } },
    animation: { pop: 'pop .5s ease backwards' } } } }
