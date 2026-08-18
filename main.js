// main.js: monta carrosséis para cada produto usando products.json
// Se products.json não existir, deixa comportamento padrão (imagem única)

document.addEventListener('DOMContentLoaded', async () => {
    let products = null;

    try {
        const res = await fetch('products.json');
        if (res.ok) products = await res.json();
    } catch (e) {
        console.warn('products.json não encontrado ou erro ao carregar:', e);
    }

    const cards = document.querySelectorAll('.product-card');

    cards.forEach(card => {
        const buyLink = card.querySelector('.buy-button');
        const productUrl = buyLink ? buyLink.href : null;

        // Tenta encontrar dados do produto pelo link
        let data = null;
        if (products && productUrl) {
            data = products.find(p => p.url && productUrl.includes(p.url)) || products.find(p => p.url === productUrl) || null;
        }

        if (!data) return; // mantém a imagem estática existente

        // Substitui a imagem única por um carrossel
        const imgEl = card.querySelector('.product-image');
        if (!imgEl) return;

        const carousel = document.createElement('div');
        carousel.className = 'carousel';

        const track = document.createElement('div');
        track.className = 'carousel-track';

        data.images.forEach((src, idx) => {
            const item = document.createElement('div');
            item.className = 'carousel-item';
            if (idx === 0) item.classList.add('active');

            const im = document.createElement('img');
            im.src = src;
            im.alt = data.title || imgEl.alt || `imagem-${idx+1}`;
            im.className = 'product-image';

            item.appendChild(im);
            track.appendChild(item);
        });

        carousel.appendChild(track);

        // controls
        const prev = document.createElement('button');
        prev.className = 'carousel-control prev';
        prev.innerText = '‹';
        const next = document.createElement('button');
        next.className = 'carousel-control next';
        next.innerText = '›';

        carousel.appendChild(prev);
        carousel.appendChild(next);

        // indicators
        const indicators = document.createElement('div');
        indicators.className = 'carousel-indicators';
        data.images.forEach((_, i) => {
            const dot = document.createElement('button');
            dot.className = 'carousel-dot' + (i===0 ? ' active' : '');
            dot.dataset.index = i;
            indicators.appendChild(dot);
        });
        carousel.appendChild(indicators);

        // product description mais completo (vindo do Amazon)
        if (data.description) {
            const descEl = card.querySelector('.product-desc');
            if (descEl) descEl.innerText = data.description;
        }

        // Replace original image with carousel
        imgEl.replaceWith(carousel);

        // Carousel logic
        let current = 0;
        const items = carousel.querySelectorAll('.carousel-item');
        const dots = carousel.querySelectorAll('.carousel-dot');

        function update(idx) {
            items.forEach((it, i) => it.classList.toggle('active', i===idx));
            dots.forEach((d,i)=> d.classList.toggle('active', i===idx));
            current = idx;
        }

        prev.addEventListener('click', () => update((current-1+items.length)%items.length));
        next.addEventListener('click', () => update((current+1)%items.length));
        dots.forEach(d => d.addEventListener('click', e => update(Number(e.currentTarget.dataset.index))));

        // touch support
        let startX = 0;
        carousel.addEventListener('touchstart', e => { startX = e.touches[0].clientX; });
        carousel.addEventListener('touchend', e => {
            const dx = (e.changedTouches[0].clientX - startX);
            if (Math.abs(dx) > 40) update(dx < 0 ? (current+1)%items.length : (current-1+items.length)%items.length);
        });
    });
});
