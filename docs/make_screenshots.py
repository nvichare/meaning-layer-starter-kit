from pathlib import Path
from textwrap import wrap
import csv, json, subprocess
from PIL import Image, ImageDraw, ImageFont

BASE = Path('/mnt/data/enterprise_ontology_practitioner_kit')
OUT = BASE/'screenshots'
OUT.mkdir(exist_ok=True)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
MONO_B = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'

# palette
NAVY=(14,35,63); BLUE=(26,100,190); TEAL=(0,135,147); GREEN=(22,132,86); AMBER=(217,137,21); RED=(184,59,60)
BG=(247,249,252); PANEL=(255,255,255); TEXT=(33,43,54); MUTED=(95,108,124); GRID=(224,230,238); PURPLE=(110,74,170)

def font(size, bold=False, mono=False):
    return ImageFont.truetype(MONO_B if mono and bold else MONO if mono else FONT_B if bold else FONT, size)

def rounded(draw, box, radius=18, fill=PANEL, outline=GRID, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def titlebar(draw,w,title,subtitle=None):
    draw.rectangle((0,0,w,92), fill=NAVY)
    draw.text((36,20), title, font=font(27,True), fill='white')
    if subtitle: draw.text((38,58), subtitle, font=font(14), fill=(205,221,239))

def arrow(draw, x1,y1,x2,y2, fill=BLUE, width=4):
    draw.line((x1,y1,x2,y2), fill=fill, width=width)
    import math
    ang=math.atan2(y2-y1,x2-x1)
    for a in (ang+2.55,ang-2.55):
        draw.line((x2,y2,x2+14*math.cos(a),y2+14*math.sin(a)), fill=fill, width=width)

def box_with_lines(draw, box, heading, lines, accent=BLUE, heading_size=18, body_size=13):
    rounded(draw,box)
    x1,y1,x2,y2=box
    draw.rounded_rectangle((x1,y1,x1+8,y2), radius=8, fill=accent)
    draw.text((x1+22,y1+17),heading,font=font(heading_size,True),fill=TEXT)
    y=y1+51
    for line in lines:
        draw.text((x1+22,y),line,font=font(body_size),fill=MUTED)
        y+=22

# 1 architecture
img=Image.new('RGB',(1600,950),BG); d=ImageDraw.Draw(img)
titlebar(d,1600,'Enterprise AI Meaning Layer: Reference Architecture','Keep formal semantics separate from catalog stewardship, then connect them through automated publication.')
# sources
for i,(h,ls,c) in enumerate([
('Operational systems',['CRM · ERP · ServiceNow','APIs · documents · events'],BLUE),
('Analytics estate',['Warehouse · lakehouse · dbt','BI · notebooks · ML features'],TEAL),
('Signals',['OpenLineage · schema drift','usage · incidents · agent logs'],PURPLE)]):
    box_with_lines(d,(45,150+i*170,330,275+i*170),h,ls,c)
# middle layers
box_with_lines(d,(430,150,800,310),'Active metadata catalog',['Atlan · OpenMetadata · Alation','glossary · lineage · ownership','workflow · discovery · adoption'],BLUE,20,14)
box_with_lines(d,(430,380,800,570),'Ontology registry',['RDF / SKOS / OWL','SHACL shapes · provenance','Git versions · persistent URIs','reasoner profile chosen explicitly'],TEAL,20,14)
box_with_lines(d,(430,650,800,825),'Publication and context service',['catalog synchronization','SPARQL / GraphQL / REST context API','policy-aware retrieval','runtime provenance in every answer'],GREEN,20,14)
# apps right
for i,(h,ls,c) in enumerate([
('AI agents',['revenue analyst','support copilot','risk investigator'],PURPLE),
('Data products',['certified metrics','customer 360','compliance views'],AMBER),
('Human workflows',['steward review','impact analysis','change approval'],GREEN)]):
    box_with_lines(d,(945,165+i*205,1515,315+i*205),h,ls,c,20,14)
# arrows
for y in [210,380,550]: arrow(d,330,y,430,y)
arrow(d,615,310,615,380); arrow(d,615,570,615,650)
arrow(d,800,735,945,240); arrow(d,800,735,945,445); arrow(d,800,735,945,650)
# feedback loop
arrow(d,1240,790,365,790,fill=RED,width=4); arrow(d,365,790,365,640,fill=RED,width=4)
d.text((915,815),'Observed usage, failures, drift and incidents generate refresh proposals',font=font(15,True),fill=RED)
img.save(OUT/'01_reference_architecture.png')

# 2 ontology graph with graphviz
ontology_dot=r'''
digraph G {
 graph [bgcolor="transparent", rankdir=LR, pad="0.4", nodesep="0.6", ranksep="0.9"];
 node [shape=box style="rounded,filled" fontname="DejaVu Sans" fontsize=14 margin="0.18,0.12" color="#dfe6ef" fontcolor="#212b36"];
 edge [fontname="DejaVu Sans" fontsize=11 color="#68778a" fontcolor="#536273" arrowsize=0.8];
 Customer [fillcolor="#e8f1ff"];
 ActiveCustomer [label="Active Customer" fillcolor="#e8f1ff"];
 NetRevenue [label="Net Revenue" fillcolor="#eefaf4"];
 PIIPolicy [label="Customer PII Policy" fillcolor="#fff3e0"];
 CustomerMaster [label="Customer Master Table" fillcolor="#f5f2ff"];
 Customer360 [label="Customer 360 View" fillcolor="#f5f2ff"];
 RevenueMart [label="Revenue Mart" fillcolor="#f5f2ff"];
 SupportCopilot [label="Support Copilot" fillcolor="#fdeff3"];
 RevenueAgent [label="Revenue Variance Agent" fillcolor="#fdeff3"];
 ActiveCustomer -> Customer [label="broader"];
 Customer -> CustomerMaster [label="implementedByAsset"];
 ActiveCustomer -> Customer360 [label="implementedByAsset"];
 NetRevenue -> RevenueMart [label="implementedByAsset"];
 NetRevenue -> Customer [label="dependsOnConcept"];
 Customer -> PIIPolicy [label="governedByPolicy"];
 CustomerMaster -> SupportCopilot [label="supportsUseCase"];
 Customer360 -> SupportCopilot [label="supportsUseCase"];
 RevenueMart -> RevenueAgent [label="supportsUseCase"];
}
'''
(BASE/'docs/ontology.dot').write_text(ontology_dot)
subprocess.run(['dot','-Tpng',str(BASE/'docs/ontology.dot'),'-o',str(OUT/'02_ontology_graph.png')],check=True)
# add title canvas around graph
graph=Image.open(OUT/'02_ontology_graph.png').convert('RGB')
canvas=Image.new('RGB',(1600,max(820,graph.height+180)),BG); dd=ImageDraw.Draw(canvas); titlebar(dd,1600,'Reference Ontology Graph','Business concepts connect to governed assets, policies and AI use cases.'); canvas.paste(graph,((1600-graph.width)//2,130)); canvas.save(OUT/'02_ontology_graph.png')

# 3 flywheel
img=Image.new('RGB',(1600,980),BG); d=ImageDraw.Draw(img); titlebar(d,1600,'Ontology Refresh Flywheel','Do not ask stewards to maintain a static glossary manually. Instrument change, propose updates, validate, approve and republish.')
steps=[
('1. Observe', 'schema drift · new tables · lineage changes\nsearch gaps · quality incidents · agent low confidence', BLUE),
('2. Propose', 'rules create deterministic proposals\nLLMs draft definitions and mappings, never approve them', PURPLE),
('3. Validate', 'SHACL constraints · OWL consistency\ncompetency queries · downstream impact analysis', TEAL),
('4. Approve', 'domain steward review · policy owner sign-off\nversioned decision record and deprecation policy', AMBER),
('5. Publish', 'release graph runtime · sync catalog terms\npropagate tags and policies through lineage', GREEN),
('6. Measure value', 'adoption · answer accuracy · reuse\ncycle time · prevented incidents · audit evidence', RED),
]
coords=[(800,210),(1170,360),(1120,665),(800,805),(455,665),(420,360)]
for idx,((heading,body,c),(cx,cy)) in enumerate(zip(steps,coords)):
    w,h=335,142; rounded(d,(cx-w//2,cy-h//2,cx+w//2,cy+h//2),22,fill=PANEL,outline=c,width=3)
    d.text((cx-w//2+20,cy-h//2+17),heading,font=font(19,True),fill=TEXT)
    y=cy-h//2+54
    for line in body.split('\n'):
        d.text((cx-w//2+20,y),line,font=font(13),fill=MUTED); y+=22
# arrows around
for i in range(len(coords)):
    x1,y1=coords[i]; x2,y2=coords[(i+1)%len(coords)]
    # stop before nodes
    import math
    dx=x2-x1; dy=y2-y1; dist=(dx*dx+dy*dy)**0.5
    sx=x1+dx*0.34; sy=y1+dy*0.34; ex=x1+dx*0.66; ey=y1+dy*0.66
    arrow(d,sx,sy,ex,ey,fill=steps[i][2],width=5)
# center
rounded(d,(630,425,970,580),30,fill=(236,243,251),outline=BLUE,width=3)
d.text((703,465),'MEANING LAYER',font=font(29,True),fill=NAVY)
d.text((694,512),'Governed, versioned, measurable',font=font(16),fill=MUTED)
img.save(OUT/'03_refresh_flywheel.png')

# helper screenshot code/terminal
def code_shot(path, title, subtitle, lines, highlights=None, size=(1600,900)):
    img=Image.new('RGB',size,(28,34,44)); d=ImageDraw.Draw(img)
    d.rectangle((0,0,size[0],80),fill=(18,23,31));
    for i,c in enumerate([(241,94,87),(245,187,78),(82,183,136)]): d.ellipse((25+i*28,27,39+i*28,41),fill=c)
    d.text((125,20),title,font=font(20,True),fill=(236,240,244))
    d.text((125,50),subtitle,font=font(13),fill=(149,163,178))
    y=110
    highlights=set(highlights or [])
    for i,line in enumerate(lines,1):
        if i in highlights: d.rectangle((72,y-3,size[0]-32,y+24), fill=(46,62,82))
        d.text((24,y),f'{i:>3}',font=font(15,mono=True),fill=(100,116,134))
        d.text((83,y),line.rstrip('\n'),font=font(15,mono=True),fill=(220,228,237))
        y+=25
        if y>size[1]-30: break
    img.save(path)

# 4 Turtle screenshot
all_lines=(BASE/'ontology/enterprise_ai.ttl').read_text().splitlines()
start=58; snippet=all_lines[start:start+27]
code_shot(OUT/'04_turtle_model_screenshot.png','enterprise_ai.ttl','SKOS term encoded in RDF/Turtle with operational review metadata',snippet, highlights=[6,7,8,9,10,11,12,13,14,15,16],size=(1600,900))
# 5 shapes screenshot
lines=(BASE/'ontology/shapes.ttl').read_text().splitlines()[5:39]
code_shot(OUT/'05_shacl_controls_screenshot.png','shapes.ttl','SHACL makes stewardship rules executable in CI and graph publication pipelines',lines, highlights=[1,2,3,4,5,6,7,8,15,16,17,18,19,20,21],size=(1600,970))
# 6 validation terminal screenshot
valid=(BASE/'docs/validation-valid.txt').read_text().splitlines()
invalid=(BASE/'docs/validation-invalid.txt').read_text().splitlines()
lines=['$ make validate',*valid,'','$ make validate-invalid  # expected to fail',*invalid[:34],'...']
code_shot(OUT/'06_validation_terminal_screenshot.png','ontology-ci','The valid graph passes; the candidate term is blocked before publication',lines,highlights=[2,4,7,13,21,29,37],size=(1600,1120))
# 7 refresh screenshot
refresh=(BASE/'docs/refresh-output.txt').read_text().splitlines()
query=(BASE/'docs/query-context.json').read_text().splitlines()
lines=['$ make refresh',*refresh,'','$ python src/query_context.py revenue',*query]
code_shot(OUT/'07_refresh_and_context_screenshot.png','meaning-layer runtime','Refresh proposals and deterministic context retrieval for agents',lines,highlights=[2,3,7,10,14,15,16],size=(1600,920))

# 8 Catalog mock screenshot
img=Image.new('RGB',(1600,940),BG); d=ImageDraw.Draw(img); titlebar(d,1600,'Illustrative Catalog Synchronization View','Original tutorial mock-up. Approved SKOS concepts are synchronized into a steward-facing catalog glossary.')
# left nav
d.rectangle((0,92,260,940),fill=(239,243,248)); d.text((28,130),'GOVERN',font=font(13,True),fill=MUTED)
for i,item in enumerate(['Glossary','Domains','Data products','Classifications','Workflows','Lineage']):
    y=174+i*54
    if item=='Glossary': d.rounded_rectangle((14,y-10,240,y+34),radius=10,fill=(219,232,249))
    d.text((35,y),item,font=font(16, item=='Glossary'),fill=NAVY if item=='Glossary' else TEXT)
# header
rounded(d,(300,132,1555,220),16,fill=PANEL); d.text((335,156),'Enterprise Business Vocabulary',font=font(25,True),fill=NAVY); d.text((335,191),'4 approved terms · synchronized from ontology release 0.1.0',font=font(14),fill=MUTED)
# table
x0,y0=300,260; cols=[('TERM',300),('STATUS',145),('STEWARD',245),('LAST REVIEW',155),('LINKED ASSETS',260)]
rounded(d,(x0,y0,1555,790),16,fill=PANEL)
x=x0+24
for label,width in cols:
    d.text((x,y0+22),label,font=font(12,True),fill=MUTED); x+=width
rows=list(csv.DictReader((BASE/'catalog_sync/glossary_terms.csv').open()))
for r,row in enumerate(rows):
    y=y0+70+r*100
    d.line((x0+20,y-12,1535,y-12),fill=GRID,width=1)
    d.text((x0+24,y),row['name'],font=font(17,True),fill=TEXT)
    d.text((x0+24,y+29),row['definition'][:63] + ('…' if len(row['definition'])>63 else ''),font=font(12),fill=MUTED)
    # status pill
    d.rounded_rectangle((x0+324,y-1,x0+409,y+27),radius=13,fill=(222,245,234)); d.text((x0+338,y+5),row['status'],font=font(12,True),fill=GREEN)
    d.text((x0+469,y+4),row['steward'],font=font(13),fill=TEXT)
    d.text((x0+714,y+4),row['last_reviewed_at'],font=font(13),fill=TEXT)
    assets=row['linked_asset_uris'].split('|') if row['linked_asset_uris'] else []
    label='Concept-only' if not assets else assets[0].split('/')[-1]
    d.text((x0+869,y+4),label,font=font(13),fill=TEXT)
# footer callout
rounded(d,(300,825,1555,900),16,fill=(232,242,252),outline=(195,217,242)); d.text((332,848),'Propagation rule',font=font(15,True),fill=NAVY); d.text((480,848),'Approved ontology terms update catalog definitions; catalog lineage pushes selected policy tags downstream.',font=font(15),fill=TEXT)
img.save(OUT/'08_catalog_sync_mock_screenshot.png')

# 9 options landscape
img=Image.new('RGB',(1600,1050),BG); d=ImageDraw.Draw(img); titlebar(d,1600,'Options Landscape: Choose Components by Responsibility','Avoid asking one product to perform every job. Combine the right catalog, modeling workbench and runtime.')
sections=[
('CATALOG AND STEWARDSHIP',150,[('Atlan','Managed active metadata catalog','Business Graph · lineage propagation · playbooks',BLUE),('OpenMetadata','Open-source context layer','glossary workflow · lineage API · open standards',TEAL),('Alation','Enterprise data intelligence catalog','glossary lifecycle · active metadata · workflow automation',PURPLE)]),
('ONTOLOGY MODELING',455,[('Protégé / WebProtégé','Open-source OWL workbench','desktop reasoning · collaborative browser editing',GREEN),('TopBraid EDG','Ontology-centered governance suite','SHACL-first modeling · linked governance assets',AMBER)]),
('GRAPH RUNTIME',700,[('Stardog','Enterprise knowledge graph platform','SHACL · reasoning · studio · virtual graphs',BLUE),('GraphDB','Semantic repository and workbench','OWL profiles · SHACL · generated GraphQL APIs',TEAL),('Jena / Fuseki or RDF4J','Open-source engineering foundation','SPARQL server · Java libraries · SHACL options',GREEN)]),
]
for heading,y,items in sections:
    d.text((60,y),heading,font=font(15,True),fill=NAVY); d.line((60,y+30,1540,y+30),fill=GRID,width=2)
    yy=y+55
    for name,kind,cap,c in items:
        rounded(d,(70,yy,1530,yy+68),14,fill=PANEL,outline=GRID); d.rounded_rectangle((70,yy,80,yy+68),radius=5,fill=c)
        d.text((100,yy+12),name,font=font(17,True),fill=TEXT); d.text((390,yy+12),kind,font=font(14),fill=MUTED); d.text((860,yy+12),cap,font=font(14),fill=TEXT)
        yy+=80
img.save(OUT/'09_options_landscape.png')

print('Generated screenshots:')
for p in sorted(OUT.glob('*.png')): print(p.name)
