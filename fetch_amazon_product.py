#!/usr/bin/env python3
"""
fetch_amazon_product.py
Busca imagens e descrição de uma página de produto Amazon e gera products.json
Uso:
    python fetch_amazon_product.py https://www.amazon.com.br/dp/B0eQwgxyG ...
Ou coloque uma URL por linha em links.txt e execute sem argumentos.

Observação: é um scraper simples e pode falhar se a Amazon bloquear requisições.
Este script é para uso local; garanta conformidade com os termos da Amazon.
"""
import sys
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/115.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
}


def extract_images(soup):
    imgs = []
    # Tenta encontrar imagens em #altImages thumbnails
    alt = soup.select('#altImages img')
    for t in alt:
        src = t.get('src')
        if src and 'data:' not in src:
            imgs.append(src)

    # Tenta data-a-dynamic-image
    if not imgs:
        main = soup.select_one('#imgTagWrapperId img')
        if main and main.get('data-a-dynamic-image'):
            try:
                j = json.loads(main['data-a-dynamic-image'])
                imgs = list(j.keys())
            except Exception:
                pass

    # fallback og:image
    if not imgs:
        meta = soup.find('meta', property='og:image')
        if meta and meta.get('content'):
            imgs = [meta['content']]

    # normalize to full-size variants when possible
    unique = []
    for u in imgs:
        if u not in unique:
            unique.append(u)

    # Try to prefer higher-resolution variants when possible
    def candidate_high_res(url):
        # Try a few replacement patterns that often map to larger images
        patterns = [
            (r'(_AC_[^._]+_)', '_SL1500_'),
            (r'(_AC_SR[0-9,]+_)', '_SL1500_'),
            (r'(_AC_SY[0-9,]+_)', '_SL1500_'),
            (r'(_SX[0-9]+_)', '_SL1500_'),
            (r'(_SY[0-9]+_)', '_SL1500_'),
            (r'(_SL[0-9]+_)', '_SL1500_'),
        ]

        candidates = []
        for pat, repl in patterns:
            try:
                cand = re.sub(pat, repl, url)
            except re.error:
                cand = url
            if cand and cand != url:
                candidates.append(cand)

        # also try removing size fragments and appending a common large suffix
        try:
            no_size = re.sub(r'\._[A-Z]{2}_[^._]+_', '.', url)
            if no_size and no_size != url:
                # insert SL1500 before extension
                parts = no_size.rsplit('.', 1)
                if len(parts) == 2:
                    candidates.append(parts[0] + '._SL1500_.' + parts[1])
        except re.error:
            pass

        # verify candidates quickly with HEAD request and prefer first that exists
        for c in candidates:
            try:
                h = requests.head(c, headers=HEADERS, allow_redirects=True, timeout=5)
                if h.status_code == 200 and 'image' in h.headers.get('Content-Type', ''):
                    return c
            except Exception:
                continue

        return url

    high_res = []
    for u in unique:
        high_res.append(candidate_high_res(u))

    # dedupe while preserving order
    seen = set()
    final = []
    for u in high_res:
        if u not in seen:
            seen.add(u)
            final.append(u)
    return final


def extract_description(soup):
    # tenta feature bullets
    bullets = soup.select('#feature-bullets li')
    if bullets:
        texts = [b.get_text(strip=True) for b in bullets]
        return '\n'.join(texts)

    # tenta productDescription
    pd = soup.select_one('#productDescription')
    if pd:
        return pd.get_text(strip=True)

    # meta description
    meta = soup.find('meta', attrs={'name': 'description'})
    if meta and meta.get('content'):
        return meta['content']

    return ''


def fetch(url):
    print('Buscando', url)
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
    except Exception as e:
        print('Erro na requisição:', e)
        return None

    if r.status_code != 200:
        print('Status code', r.status_code)
        return None

    soup = BeautifulSoup(r.text, 'html.parser')
    title = ''
    t = soup.select_one('#productTitle')
    if t:
        title = t.get_text(strip=True)

    images = extract_images(soup)
    description = extract_description(soup)

    return {'url': url, 'title': title, 'images': images, 'description': description}


def main():
    urls = sys.argv[1:]
    if not urls:
        f = Path('links.txt')
        if f.exists():
            urls = [l.strip() for l in f.read_text(encoding='utf-8').splitlines() if l.strip()]

    if not urls:
        print('Passe URLs como argumentos ou coloque links em links.txt')
        sys.exit(1)

    results = []
    for u in urls:
        res = fetch(u)
        if res:
            results.append(res)

    out = Path('products.json')
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Salvo em', out)


if __name__ == '__main__':
    main()
