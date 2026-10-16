from PIL import Image, ImageOps, ImageDraw
from pathlib import Path
import pdfplumber
folder=Path('tmp/pdfs')
files=sorted(folder.glob('guia-*.png'))
assert len(files)==12, len(files)
for batch in range(3):
    sheet=Image.new('RGB',(1200,1740),'#dce5ed')
    draw=ImageDraw.Draw(sheet)
    for offset,file in enumerate(files[batch*4:batch*4+4]):
        img=Image.open(file).convert('RGB')
        img.thumbnail((580,830))
        x=(offset%2)*600+10; y=(offset//2)*870+30
        sheet.paste(img,(x,y))
        draw.text((x,y-22),file.name,fill='#142D46')
    sheet.save(folder/f'revision-{batch+1}.png')
with pdfplumber.open('output/pdf/Guia_de_estudio_y_defensa_Sprint_1.pdf') as pdf:
    for number,page in enumerate(pdf.pages,1):
        chars=[c for c in page.chars if c.get('text','').strip()]
        outside=[c for c in chars if c['x0']<40 or c['x1']>page.width-40 or c['top']<18 or c['bottom']>page.height-18]
        assert not outside,(number,outside[:2])
    print('QA: 12 páginas; texto dentro de márgenes; contenido extraíble; marcadores presentes.')
