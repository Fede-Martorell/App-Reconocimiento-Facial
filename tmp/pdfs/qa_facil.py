from PIL import Image, ImageDraw
from pathlib import Path
import pdfplumber
files=sorted(Path('tmp/pdfs').glob('facil-*.png'))
assert len(files)==6
for batch in range(2):
    sheet=Image.new('RGB',(1800,900),'#dce5ed')
    for i,file in enumerate(files[batch*3:batch*3+3]):
        im=Image.open(file).convert('RGB'); im.thumbnail((580,850)); sheet.paste(im,(i*600+10,25))
    sheet.save(f'tmp/pdfs/facil-revision-{batch+1}.png')
with pdfplumber.open('output/pdf/Guia_facil_Sprint_1.pdf') as pdf:
    for n,p in enumerate(pdf.pages,1):
        for c in p.chars:
            if c['text'].strip(): assert c['x0']>=40 and c['x1']<=p.width-40 and c['top']>=18 and c['bottom']<=p.height-18,(n,c)
print('Márgenes y seis páginas verificados.')
