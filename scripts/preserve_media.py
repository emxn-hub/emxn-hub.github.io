import pathlib, re, html, urllib.request, urllib.parse, concurrent.futures
root=pathlib.Path('.')
pages=list(root.rglob('index.html'))
pattern=re.compile(r'https://(?:i[0-9]\\.wp\\.com/)?shiny-face-widget\\.wpcomstaging\\.com/wp-content/uploads/[^\\s"\\'<>;&?]+(?:\\?[^"\\'<>\\s]*)?')
# Match original media paths and strip image transformation parameters.
pattern=re.compile(r'https://(?:i[0-9]\.wp\.com/)?shiny-face-widget\.wpcomstaging\.com/wp-content/uploads/[^\s"'<>?;]+(?:\?[^"\s<>]*)?')
def key(url):
    return html.unescape(url).split('?')[0].split('/wp-content/uploads/',1)[1]
urls={}
for p in pages:
    for m in pattern.finditer(p.read_text()):
        urls.setdefault(key(m.group()),html.unescape(m.group()))
def download(item):
    k,u=item
    dest=root/'assets'/k
    dest.parent.mkdir(parents=True,exist_ok=True)
    for candidate in ['https://shiny-face-widget.wpcomstaging.com/wp-content/uploads/'+k,'https://i0.wp.com/shiny-face-widget.wpcomstaging.com/wp-content/uploads/'+k,u]:
        try:
            req=urllib.request.Request(candidate,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=40) as response:
                data=response.read()
                typ=response.headers.get_content_type()
            if not (typ.startswith('image/') or data.startswith(b'%PDF-')) or not data: continue
            dest.write_bytes(data)
            print('Copied',k,flush=True)
            return k
        except Exception as e: print(k,str(e),flush=True)
    return None
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    done=set(pool.map(download,urls.items()))
for p in pages:
    s=p.read_text()
    s=pattern.sub(lambda m:'/assets/'+key(m.group()) if key(m.group()) in done else m.group(),s)
    p.write_text(s)
print('Copied',len(done-{None}),'of',len(urls),'referenced assets')
if not done-{None}: raise SystemExit('No assets could be downloaded')
