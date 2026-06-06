from pathlib import Path
from datetime import date
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE

ROOT = Path('/mnt/data/enterprise_ontology_practitioner_kit')
OUT = Path('/mnt/data/enterprise_ai_ontology_practitioner_guide.docx')

NAVY = '0D2746'
BLUE = '1769AA'
TEAL = '0F766E'
GREEN = '237A57'
PURPLE = '6D4BC1'
ORANGE = 'C96B16'
LIGHT_BLUE = 'EAF3FB'
LIGHT_TEAL = 'EAF7F5'
LIGHT_GRAY = 'F3F6F9'
MED_GRAY = 'DCE4EC'
DARK_GRAY = '35475A'
RED = 'A33A3A'


def set_cell_shading(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd')
        tcPr.append(shd)
    shd.set(qn('w:fill'), fill)


def set_cell_border(cell, **kwargs):
    """Set cell borders. kwargs examples: top={'sz':'4','val':'single','color':'D9E2F3'}"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in('w:tcBorders')
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('top','left','bottom','right','insideH','insideV'):
        if edge in kwargs:
            tag = 'w:{}'.format(edge)
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key in ['val','sz','space','color']:
                if key in kwargs[edge]:
                    element.set(qn('w:{}'.format(key)), str(kwargs[edge][key]))


def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement('w:tblHeader')
    tblHeader.set(qn('w:val'), 'true')
    trPr.append(tblHeader)


def set_cell_margins(cell, top=70, start=80, bottom=70, end=80):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = tcPr.first_child_found_in('w:tcMar')
    if tcMar is None:
        tcMar = OxmlElement('w:tcMar')
        tcPr.append(tcMar)
    for m, v in [('top',top),('start',start),('bottom',bottom),('end',end)]:
        node = tcMar.find(qn(f'w:{m}'))
        if node is None:
            node = OxmlElement(f'w:{m}')
            tcMar.append(node)
        node.set(qn('w:w'), str(v))
        node.set(qn('w:type'), 'dxa')


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run('Page ')
    run.font.size = Pt(8)
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = ' PAGE '
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)


def set_run_font(run, name='Aptos', size=10.0, bold=False, color=None, italic=False):
    run.font.name = name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def add_para(doc, text='', style=None, align=None, space_after=3, space_before=0, line_spacing=1.05, keep=False):
    p = doc.add_paragraph(style=style)
    if text:
        r = p.add_run(text)
        set_run_font(r, size=9.5)
    fmt = p.paragraph_format
    fmt.space_after = Pt(space_after)
    fmt.space_before = Pt(space_before)
    fmt.line_spacing = line_spacing
    fmt.keep_together = keep
    if align is not None:
        p.alignment = align
    return p


def add_bullet(doc, text, level=0, bold_prefix=None):
    style = 'List Bullet' if level == 0 else 'List Bullet 2'
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(1.5)
    p.paragraph_format.line_spacing = 1.0
    if bold_prefix and text.startswith(bold_prefix):
        r1=p.add_run(bold_prefix); set_run_font(r1,size=9.2,bold=True,color=NAVY)
        r2=p.add_run(text[len(bold_prefix):]); set_run_font(r2,size=9.2)
    else:
        r=p.add_run(text); set_run_font(r,size=9.2)
    return p


def add_number(doc, text, level=0):
    style = 'List Number' if level == 0 else 'List Number 2'
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(1.5)
    p.paragraph_format.line_spacing = 1.0
    r=p.add_run(text); set_run_font(r,size=9.2)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_paragraph(style=f'Heading {level}')
    p.paragraph_format.space_before = Pt(8 if level == 1 else 5)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    set_run_font(r, size={1:16,2:12.2,3:10.6}.get(level,10), bold=True, color=NAVY if level<3 else BLUE)
    return p


def add_callout(doc, title, body, fill=LIGHT_BLUE, accent=BLUE):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    cell = table.cell(0,0)
    set_cell_shading(cell, fill)
    set_cell_border(cell, left={'sz':'20','val':'single','color':accent}, top={'sz':'2','val':'single','color':MED_GRAY}, bottom={'sz':'2','val':'single','color':MED_GRAY}, right={'sz':'2','val':'single','color':MED_GRAY})
    set_cell_margins(cell, top=90, bottom=90, start=125, end=125)
    p=cell.paragraphs[0]
    p.paragraph_format.space_after=Pt(2)
    r=p.add_run(title); set_run_font(r,size=9.4,bold=True,color=NAVY)
    p2=cell.add_paragraph()
    p2.paragraph_format.space_after=Pt(0); p2.paragraph_format.line_spacing=1.0
    r=p2.add_run(body); set_run_font(r,size=9.0,color=DARK_GRAY)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def add_table(doc, headers, rows, widths=None, font_size=8.4, header_fill=NAVY):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'
    table.autofit = False
    hdr = table.rows[0]
    set_repeat_table_header(hdr)
    for i,h in enumerate(headers):
        cell=hdr.cells[i]
        set_cell_shading(cell,header_fill)
        set_cell_margins(cell)
        cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p=cell.paragraphs[0]; p.paragraph_format.space_after=Pt(0)
        r=p.add_run(h); set_run_font(r,size=font_size,bold=True,color='FFFFFF')
        if widths: cell.width=Inches(widths[i])
    for ridx,row in enumerate(rows):
        cells=table.add_row().cells
        for i,val in enumerate(row):
            cell=cells[i]
            set_cell_margins(cell)
            if ridx % 2 == 1: set_cell_shading(cell, 'F8FAFC')
            cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.TOP
            p=cell.paragraphs[0]; p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing=1.0
            r=p.add_run(str(val)); set_run_font(r,size=font_size,color='24384D')
            if widths: cell.width=Inches(widths[i])
    doc.add_paragraph().paragraph_format.space_after=Pt(0)
    return table


def add_code(doc, code, title=None, max_lines=None):
    if title:
        p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(1)
        r=p.add_run(title); set_run_font(r,size=8.8,bold=True,color=BLUE)
    lines=code.strip('\n').splitlines()
    if max_lines and len(lines)>max_lines:
        lines=lines[:max_lines]+['# ... excerpt truncated; see the included repository for the complete file']
    table=doc.add_table(rows=1,cols=1)
    table.alignment=WD_TABLE_ALIGNMENT.CENTER
    cell=table.cell(0,0)
    set_cell_shading(cell,'152131')
    set_cell_border(cell, top={'sz':'2','val':'single','color':'24364D'}, bottom={'sz':'2','val':'single','color':'24364D'}, left={'sz':'2','val':'single','color':'24364D'}, right={'sz':'2','val':'single','color':'24364D'})
    set_cell_margins(cell, top=90,bottom=90,start=110,end=110)
    p=cell.paragraphs[0]; p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing=0.95
    for idx,line in enumerate(lines):
        if idx:
            p.add_run('\n')
        r=p.add_run(line); set_run_font(r,name='Liberation Mono',size=7.5,color='E6EDF3')
    doc.add_paragraph().paragraph_format.space_after=Pt(0)
    return table


def add_figure(doc, filename, caption, width=6.85):
    p=doc.add_paragraph()
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after=Pt(1)
    r=p.add_run(); r.add_picture(str(ROOT/'screenshots'/filename), width=Inches(width))
    cp=doc.add_paragraph()
    cp.alignment=WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after=Pt(4)
    rr=cp.add_run(caption)
    set_run_font(rr,size=7.6,italic=True,color=DARK_GRAY)


def new_page(doc):
    doc.add_page_break()


def read(rel):
    return (ROOT/rel).read_text()

# --- Document setup ---
doc=Document()
sec=doc.sections[0]
sec.top_margin=Inches(0.55); sec.bottom_margin=Inches(0.55); sec.left_margin=Inches(0.62); sec.right_margin=Inches(0.62)

styles=doc.styles
styles['Normal'].font.name='Aptos'; styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'),'Aptos'); styles['Normal'].font.size=Pt(9.5)
for name,size,color in [('Heading 1',16,NAVY),('Heading 2',12.2,NAVY),('Heading 3',10.6,BLUE)]:
    st=styles[name]; st.font.name='Aptos Display'; st._element.rPr.rFonts.set(qn('w:eastAsia'),'Aptos Display'); st.font.size=Pt(size); st.font.bold=True; st.font.color.rgb=RGBColor.from_string(color)

# Header / footer
header=sec.header.paragraphs[0]
header.alignment=WD_ALIGN_PARAGRAPH.RIGHT
r=header.add_run('ENTERPRISE AI ONTOLOGIES  |  PRACTITIONER GUIDE')
set_run_font(r,size=7.5,bold=True,color=BLUE)
footer=sec.footer.paragraphs[0]
r=footer.add_run('Living meaning layers for governed enterprise AI')
set_run_font(r,size=7.5,color=DARK_GRAY)
add_page_number(sec.footer.add_paragraph())

# Core props
props=doc.core_properties
props.title='Enterprise AI Ontologies: A Practitioner\'s Guide'
props.subject='RDF, SKOS, OWL, SHACL, catalog synchronization and ontology refresh flywheels'
props.author='OpenAI'
props.keywords='enterprise ontology, RDF, OWL, SKOS, SHACL, enterprise AI, data catalog, Atlan, OpenMetadata, Alation'

# Cover
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(18); p.paragraph_format.space_after=Pt(8)
r=p.add_run('ENTERPRISE AI ONTOLOGIES'); set_run_font(r,size=27,bold=True,color=NAVY)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(5)
r=p.add_run("A Practitioner\'s Guide to Building a Living Meaning Layer"); set_run_font(r,size=15,bold=True,color=BLUE)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(13)
r=p.add_run('RDF  |  SKOS  |  OWL  |  SHACL  |  Catalog Synchronization  |  Refresh Flywheels'); set_run_font(r,size=9.3,bold=True,color=DARK_GRAY)
add_figure(doc,'01_reference_architecture.png','Cover illustration. Reference architecture for an enterprise AI meaning layer. Original tutorial illustration; not a vendor user interface.',width=6.95)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(9); p.paragraph_format.space_after=Pt(2)
r=p.add_run('Implementation guide and executable starter kit'); set_run_font(r,size=11.3,bold=True,color=NAVY)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run('Prepared June 2026  |  Official documentation reviewed June 5, 2026'); set_run_font(r,size=8.8,color=DARK_GRAY)

new_page(doc)

# Orientation
add_heading(doc,'How to use this guide',1)
add_callout(doc,'Executive position','Do not ask an LLM to invent enterprise meaning at runtime. Use AI to accelerate discovery, mapping, and change proposals. Keep approved business meaning in a governed semantic layer with stable identifiers, explicit definitions, validation rules, ownership, versioning, and catalog propagation.',fill=LIGHT_BLUE,accent=BLUE)
add_para(doc,'This guide is intentionally pragmatic. It starts with a lightweight business vocabulary and only adds formal OWL semantics where inference produces measurable value. It also separates two purchasing decisions that are frequently conflated: the catalog layer used by teams for discovery and stewardship, and the ontology runtime used for machine-readable semantics, validation, and reasoning.')
add_para(doc,'Naming note: the request referenced “Ellation.” This guide assumes the intended vendor is Alation. Validate that assumption before using the procurement scorecard.')
add_heading(doc,'Guide map',2)
contents=[
('1','What you are building','A living meaning layer, not a static glossary'),
('2','Standards and modeling choices','RDF, SKOS, OWL, SHACL, PROV-O'),
('3','Build the minimum viable ontology','Concept selection, URIs, examples and controls'),
('4','Run the executable starter kit','Code, validation, refresh proposals and context API'),
('5','Design the refresh flywheel','How the ontology stays current'),
('6','Propagate meaning across the enterprise','Catalogs, lineage, semantic models and AI applications'),
('7','Options analysis','Atlan, OpenMetadata, Alation and ontology-native tools'),
('8','Scale through an operating model','Release process, accountability, KPIs and 12-week plan'),
('9','Production hardening checklist','What to complete before scale-out'),
('A','Sources and starter-kit inventory','Official documentation and included files'),
]
add_table(doc,['Section','Topic','Outcome'],contents,widths=[0.55,2.25,4.35],font_size=8.4)

# Section 1
new_page(doc)
add_heading(doc,'1. What you are building',1)
add_para(doc,'Enterprise AI needs a controlled source of meaning. Data catalogs, metric stores, semantic layers, knowledge graphs, policies, and LLM prompts each solve part of the problem. An ontology connects those components by assigning stable identifiers to business concepts and by making their relationships, definitions, owners, controls, and implementations explicit.')
add_heading(doc,'1.1 Separate the layers',2)
rows=[
('Glossary','Human-readable definition of terms such as Customer, Active Customer, Net Revenue and Product.','Alignment and search.'),
('Taxonomy','Hierarchies and classification schemes.','Navigation, tagging and domain organization.'),
('Ontology','Formal concepts, relationships, constraints and selected inference rules.','Machine-readable meaning and controlled reasoning.'),
('Semantic layer','Executable metrics and entity logic exposed to BI and AI applications.','Consistent calculation and query behavior.'),
('Catalog','Stewardship interface, discovery, lineage, workflows and metadata propagation.','Adoption across teams.'),
('Graph runtime','Store, query, validate and optionally reason over RDF.','Runtime context and machine integration.'),
]
add_table(doc,['Layer','Purpose','Primary business outcome'],rows,widths=[1.05,3.8,2.3],font_size=8.4)
add_heading(doc,'1.2 Use a layered architecture',2)
add_para(doc,'The recommended pattern is a thin governed ontology registry at the center. Operational signals and analytics signals create proposals. Stewards approve releases. A publication layer synchronizes approved terms to catalogs and exposes context to AI agents, data products, semantic models, and human workflows. The catalog remains the primary collaboration surface; the ontology registry remains the portable semantic source of truth.')
add_figure(doc,'01_reference_architecture.png','Figure 1. Reference architecture. Original tutorial illustration; not a vendor user interface.',width=6.85)
add_heading(doc,'1.3 Pick a bounded first use case',2)
add_para(doc,'Begin with one business decision where inconsistent meaning has a visible cost. Good starting points include revenue reporting, customer eligibility, product hierarchy, incident management, contract entitlements, and regulatory classification. Select 25 to 75 concepts, not 5,000. The first release must answer concrete questions.')
add_bullet(doc,'Example competency questions: What qualifies as an active customer? Which data asset implements the approved definition? Which downstream dashboards and agents would be affected by a definition change? Who owns the approval?')
add_bullet(doc,'Example runtime question: What calculation, source asset, steward, policy and approved version should an AI revenue analyst use when asked for net revenue?')
add_callout(doc,'Rule of thumb','If a relationship does not improve a decision, validation control, lineage impact analysis, search experience, or AI answer, postpone it. Ontology programs fail when modeling scope outruns operational value.',fill=LIGHT_TEAL,accent=TEAL)

# Section 2
new_page(doc)
add_heading(doc,'2. Standards and modeling choices',1)
add_para(doc,'Use the W3C standards as complementary tools rather than as competing choices. RDF provides graph statements. SKOS represents business vocabularies. OWL adds formal semantics where inference is worth the complexity. SHACL validates graph quality and governance contracts. PROV-O records how releases and proposals were generated. [S1-S5]')
rows=[
('RDF','Portable graph statements expressed as subject-predicate-object triples.','Always. This is the interoperable base.'),
('SKOS','Concept schemes, preferred labels, alternative labels, definitions and broader/narrower relationships.','Use for the catalog-facing vocabulary.'),
('OWL','Classes, properties, restrictions and inferencing semantics.','Add selectively where reasoning supports a use case.'),
('SHACL','Shapes that validate required fields and business rules over RDF graphs.','Use from the first release as a CI and publication gate.'),
('PROV-O','Provenance model for entities, activities and agents.','Use for proposal and release traceability.'),
]
add_table(doc,['Standard','What it contributes','Recommended posture'],rows,widths=[0.85,3.2,3.1],font_size=8.4)
add_heading(doc,'2.1 Model business vocabulary with SKOS first',2)
add_para(doc,'A lightweight business vocabulary is easier to govern and easier to synchronize into a catalog. The starter ontology models Customer, Active Customer, Net Revenue and Customer PII Policy as SKOS concepts with preferred labels, definitions, stewards, review cadences and implementation links.')
add_code(doc,'''ex:NetRevenueTerm a skos:Concept, ex:MetricConcept ;
  skos:inScheme ex:EnterpriseBusinessVocabulary ;
  skos:prefLabel "Net Revenue"@en ;
  skos:definition "Recognized gross revenue less contractual discounts, returns, credits, and rebates."@en ;
  ex:calculationLogic "SUM(gross_revenue - discounts - returns - credits - rebates)" ;
  ex:steward "Finance Analytics" ;
  ex:status "Approved" ;
  ex:lastReviewedAt "2026-04-15"^^xsd:date ;
  ex:reviewCadenceDays 60 ;
  ex:implementedByAsset ex:RevenueMart .''','Turtle excerpt: ontology/enterprise_ai.ttl')
add_heading(doc,'2.2 Add OWL only where reasoning matters',2)
add_para(doc,'OWL is useful when your application benefits from inferences such as class membership, transitive relationships, equivalence, disjointness, or controlled restrictions. Avoid starting with an overly expressive model. For high-volume operational reasoning, prefer the OWL 2 RL profile or another bounded rule set supported by your runtime. [S3]')
add_bullet(doc,'Appropriate OWL example: infer that a restricted customer data asset is governed by a privacy policy through modeled relationships.')
add_bullet(doc,'Poor first use: encode every exception from a policy manual as deeply nested logical axioms before you have an application consuming them.')
add_heading(doc,'2.3 Treat SHACL as executable governance',2)
add_para(doc,'SHACL turns stewardship rules into testable controls. A term is not publishable simply because an LLM generated a plausible definition. It must meet a contract: label, definition, steward, lifecycle status, review date, review cadence, calculation logic for metrics, and ownership for data assets.')
add_code(doc,'''ex:MetricConceptShape a sh:NodeShape ;
  sh:targetClass ex:MetricConcept ;
  sh:property [
    sh:path ex:calculationLogic ;
    sh:minCount 1 ;
    sh:message "A governed metric requires deterministic calculation logic." ;
  ] ;
  sh:property [
    sh:path ex:implementedByAsset ;
    sh:minCount 1 ;
    sh:message "A governed metric must link to at least one implementing data asset." ;
  ] .''','Turtle excerpt: ontology/shapes.ttl')
add_figure(doc,'05_shacl_controls_screenshot.png','Figure 2. SHACL controls in the included starter kit. Original code screenshot.',width=6.65)

# Section 3
new_page(doc)
add_heading(doc,'3. Build the minimum viable ontology',1)
add_heading(doc,'3.1 Define a compact concept record',2)
add_para(doc,'Use one stable URI per concept and separate the concept identity from its mutable attributes. The concept URI should not embed a version number. Releases should carry versions. Deprecate concepts rather than deleting them, and link replacements explicitly.')
rows=[
('Identity','URI, preferred label, alternative labels, definition','Stable lookup and search.'),
('Governance','steward, status, approval workflow, last review date, review cadence','Accountability and freshness.'),
('Implementation','source assets, semantic model, calculation logic, catalog ID','Executable use in analytics and AI.'),
('Relationships','broader concept, dependencies, policies, supported use cases','Impact analysis and retrieval.'),
('Provenance','proposal, reviewer, release, effective date, superseded release','Auditability and rollback.'),
]
add_table(doc,['Facet','Minimum fields','Why it matters'],rows,widths=[1.0,3.5,2.65],font_size=8.4)
add_heading(doc,'3.2 Establish URI and versioning rules',2)
add_bullet(doc,'Use a controlled HTTPS namespace such as https://ontology.company.com/finance/NetRevenue. Do not use database names as concept identities.')
add_bullet(doc,'Version releases using semantic versioning or a release date. Increment major versions for breaking semantic changes, minor versions for additive concepts or relationships, and patch versions for non-breaking metadata corrections.')
add_bullet(doc,'Keep aliases and deprecated concepts so older dashboards, prompts and APIs can resolve meaning during migration.')
add_bullet(doc,'Record catalog IDs separately because catalog object identifiers can change during platform migrations.')
add_heading(doc,'3.3 Connect meaning to implementations',2)
add_para(doc,'A business ontology becomes operational when every important concept is mapped to the assets and APIs that implement it. A revenue metric should point to its semantic model or governed mart. A customer concept should point to the master table, quality checks and privacy policy. A support agent should point to the approved context bundle rather than a prompt-only definition.')
add_figure(doc,'02_ontology_graph.png','Figure 3. Reference ontology graph linking concepts, assets, policies and AI use cases. Original tutorial illustration.',width=6.85)
add_heading(doc,'3.4 Use AI as a proposal engine, not as the publisher',2)
add_para(doc,'AI can cluster search logs, draft definitions, identify synonyms, map schema changes, detect stale terms and propose relationships. It should not silently publish semantic changes. Proposals should pass SHACL checks, lineage impact analysis, domain review and release approval before propagation.')
add_callout(doc,'Required control boundary','AI-assisted discovery -> proposed change -> validation -> steward approval -> versioned release -> catalog and runtime synchronization -> monitoring. Never skip the approval and release boundary for meaning that affects decisions.',fill='FFF4E8',accent=ORANGE)

# Section 4
new_page(doc)
add_heading(doc,'4. Run the executable starter kit',1)
add_para(doc,'The included repository is deliberately small enough to understand in one sitting. It demonstrates portable RDF/Turtle modeling, SKOS vocabulary design, SHACL validation, refresh proposal generation, catalog exports, a dry-run OpenMetadata adapter, an Atlan CSV export and an agent-facing context API.')
add_heading(doc,'4.1 Quick start',2)
add_code(doc,'''python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make validate
make validate-invalid   # expected to fail
make query
make refresh
make export
make sync-openmetadata  # dry-run payloads
make sync-atlan         # writes CSV
make api                # local FastAPI endpoint''','Run from the enterprise_ontology_practitioner_kit directory')
add_heading(doc,'4.2 Inspect the RDF vocabulary',2)
add_para(doc,'Open ontology/enterprise_ai.ttl in Protégé, VS Code, or another RDF-aware editor. Protégé is a free open-source ontology editor and is a practical starting point for domain model development. [S6]')
add_figure(doc,'04_turtle_model_screenshot.png','Figure 4. Turtle vocabulary excerpt from the included repository. Original code screenshot.',width=6.65)
add_heading(doc,'4.3 Validate before publication',2)
add_para(doc,'The valid sample passes 167 triples. The intentionally weak sample fails with six violations: an invalid lifecycle status, a missing implemented asset, missing deterministic calculation logic, missing asset steward, missing asset type and an invalid review cadence. This is the core operational discipline: a model change is testable.')
add_code(doc,read('docs/validation-valid.txt')+'\n\n# Deliberately invalid sample\n'+read('docs/validation-invalid.txt'), 'Observed execution results', max_lines=29)
add_figure(doc,'06_validation_terminal_screenshot.png','Figure 5. Passing and failing SHACL runs. Original terminal screenshot from the included repository.',width=6.65)
add_heading(doc,'4.4 Query approved context for an AI application',2)
add_para(doc,'The context API pattern keeps an AI application from inventing business meaning. At runtime, retrieve an approved context bundle with the concept definition, steward, lifecycle status, calculation logic and implementing asset. The assistant can cite this bundle or refuse the task if no approved context exists.')
add_code(doc,read('docs/query-context.json'),'Observed context lookup for “revenue”',max_lines=22)
add_heading(doc,'4.5 Generate refresh proposals',2)
add_para(doc,'The refresh script identifies overdue reviews and creates a proposal, not an automatic edit. Replace the demo date logic with event ingestion from your catalog, lineage service, schema registry, semantic models, BI usage logs and agent observability stack.')
add_code(doc,read('docs/refresh-output.txt'),'Observed refresh proposal output')
add_figure(doc,'07_refresh_and_context_screenshot.png','Figure 6. Refresh proposal and agent context retrieval. Original terminal screenshot from the included repository.',width=6.65)

# Section 5
new_page(doc)
add_heading(doc,'5. Design the refresh flywheel',1)
add_para(doc,'Ontology stagnation is an operating-model failure, not a modeling-language failure. A living meaning layer needs event-driven proposals, time-based review cadences, human approval, automated publication, and usage measurement. The process is a flywheel because consumption creates signals that improve the next release.')
add_figure(doc,'03_refresh_flywheel.png','Figure 7. Ontology refresh flywheel. Original tutorial illustration.',width=6.85)
add_heading(doc,'5.1 Observe the right signals',2)
rows=[
('Schema drift','Columns added, renamed, dropped or type-changed.','Propose impacted concept-to-asset mapping reviews.'),
('Lineage drift','Upstream/downstream lineage or semantic model dependency changed.','Run impact analysis and create targeted stewardship tasks.'),
('Search behavior','No-result searches, repeated synonym searches, abandoned searches.','Propose terms, aliases and definition improvements.'),
('AI observability','Low-confidence answers, answer disagreement, repeated clarification, retrieval misses.','Propose missing concepts, relationships or context bundles.'),
('Quality incidents','Data-quality failures, policy violations, BI reconciliations.','Reopen affected concepts and implementing assets.'),
('Usage analytics','Unused terms, highly used terms, new products and new domains.','Prioritize maintenance and expansion.'),
('Time cadence','Review date exceeded for a term, metric or policy.','Create periodic steward review task.'),
]
add_table(doc,['Signal','Example','Automated response'],rows,widths=[1.15,2.6,3.4],font_size=8.2)
add_heading(doc,'5.2 Use a controlled state machine',2)
add_para(doc,'Use lifecycle states that match your governance model. A practical minimum is Draft -> In Review -> Approved -> Deprecated. The ontology source can remain Git-backed even when the user-facing workflow occurs in a catalog. The approved release is the only version published to production endpoints.')
add_heading(doc,'5.3 Propagate approved releases',2)
add_bullet(doc,'Publish RDF to the graph runtime and refresh its indexes or reasoning materialization.')
add_bullet(doc,'Synchronize glossary terms, aliases, owners, policies, and ontology URIs into the catalog.')
add_bullet(doc,'Update semantic model documentation and metric APIs with the approved version identifier.')
add_bullet(doc,'Invalidate or refresh agent context caches. Keep prior versions available for traceability.')
add_bullet(doc,'Use lineage to identify dashboards, features, data products and agents that require regression tests.')
add_heading(doc,'5.4 Measure whether the flywheel creates value',2)
rows=[
('Trust','Percentage of top business metrics with approved definitions, owners and implementations.'),
('Freshness','Percentage of active concepts within review cadence; mean time to approve high-impact changes.'),
('Reuse','Number of dashboards, APIs and agents consuming approved context bundles.'),
('Answer quality','Reduction in AI retrieval misses, clarification turns and semantic-answer disagreement.'),
('Change safety','Percentage of semantic changes with lineage impact analysis and regression evidence.'),
('Productivity','Time to onboard a new data product, agent or domain using existing concepts.'),
]
add_table(doc,['Value dimension','Example KPI'],rows,widths=[1.45,5.7],font_size=8.4)

# Section 6
new_page(doc)
add_heading(doc,'6. Propagate meaning across the enterprise',1)
add_heading(doc,'6.1 Treat the catalog as the collaboration surface',2)
add_para(doc,'The catalog should make approved meanings visible where teams already discover data. Synchronize the preferred label, definition, synonyms, owner, lifecycle state, ontology URI, policy relationships, and implementing assets. Use catalog workflows to collect proposals and route approvals. Preserve the canonical URI so the organization can change catalog products without losing semantic identity.')
add_figure(doc,'08_catalog_sync_mock_screenshot.png','Figure 8. Illustrative synchronized catalog view. This is an original tutorial mockup, not an Atlan, OpenMetadata or Alation user interface.',width=6.85)
add_heading(doc,'6.2 Keep catalog synchronization adapters simple',2)
add_para(doc,'The starter kit exports a canonical glossary CSV, prints OpenMetadata glossary-term payloads in dry-run mode, and creates an Atlan Business Graph import CSV. Review the payload shape against your tenant version and security model before enabling write operations.')
add_code(doc,'''make export
make sync-openmetadata   # dry run: inspect JSON payloads before enabling writes
make sync-atlan          # inspect catalog_sync/atlan_business_graph_import.csv

# Production pattern
# 1. Export approved release.
# 2. Diff against previous catalog state.
# 3. Apply only approved changes.
# 4. Persist the catalog response identifiers.
# 5. Emit an audit event and refresh dependent caches.''','Catalog synchronization pattern')
add_heading(doc,'6.3 Publish an agent context contract',2)
add_para(doc,'Use a dedicated context endpoint or tool rather than embedding mutable definitions in prompts. The endpoint should return the ontology URI, approved release, definition, calculation logic, policy constraints, owner, asset references and effective date. Log which context version was used for every consequential AI action.')
add_code(doc,'''GET /concepts/search?q=revenue

[
  {
    "concept_uri": "https://example.com/enterprise-ai/NetRevenueTerm",
    "label": "Net Revenue",
    "definition": "Recognized gross revenue less contractual discounts, returns, credits, and rebates.",
    "status": "Approved",
    "calculation_logic": "SUM(gross_revenue - discounts - returns - credits - rebates)",
    "catalog_id": "snowflake.finance.revenue_mart"
  }
]''','Agent context response excerpt')
add_heading(doc,'6.4 Add regression tests for semantic releases',2)
add_bullet(doc,'Run SHACL validation on the ontology and mapped assets.')
add_bullet(doc,'Execute SPARQL competency queries and compare expected results.')
add_bullet(doc,'Run metric reconciliation tests against approved reference outputs.')
add_bullet(doc,'Run retrieval and agent-answer tests on a golden evaluation set.')
add_bullet(doc,'Check lineage impact scope and require explicit acknowledgement for high-risk consumers.')

# Section 7
new_page(doc)
add_heading(doc,'7. Options analysis',1)
add_para(doc,'Evaluate products by responsibility. Atlan, OpenMetadata and Alation are catalog-layer choices. Protégé and TopBraid EDG support ontology modeling and stewardship. Stardog, GraphDB, Apache Jena/Fuseki, Eclipse RDF4J and Ontop serve graph-runtime or integration needs. A single product may cover multiple responsibilities, but the procurement scorecard should not assume a catalog is an OWL reasoning engine.')
add_figure(doc,'09_options_landscape.png','Figure 9. Options landscape by responsibility. Original tutorial illustration.',width=6.85)
add_heading(doc,'7.1 Catalog-layer comparison: Atlan, OpenMetadata and Alation',2)
rows=[
('Atlan','Business Graph glossary with terms and categories; terms can be related and attached to assets.','Lineage capability plus Metadata Propagator for selected metadata through lineage, hierarchy or named relationships; Playbooks automate metadata updates at scale.','Strong managed collaboration layer. Pair with a separate RDF/OWL registry and runtime when formal ontology validation or reasoning is required.','Validate tenant APIs, events, glossary import/export and how ontology URIs are persisted. [S15-S18]'),
('OpenMetadata','Glossary hierarchy, synonyms, related terms and governance workflows.','Lineage API; glossary approval workflow; APIs and an open-source codebase.','Strong choice when open-source control and customization matter. Current documentation explicitly describes canonical schemas alongside RDF/OWL models, SHACL shapes, JSON-LD and PROV-O.','Validate deployed version, standards coverage in your use cases, workflow maturity and operational support model. [S19-S22]'),
('Alation','Enterprise catalog and glossary capabilities with documentation, governance and collaboration.','Workflow Automation covers catalog, governance and compliance tasks; catalog experience emphasizes metadata, governance and lineage.','Strong managed catalog candidate for broad enterprise adoption. Pair with a separate ontology registry/runtime for formal RDF/OWL semantics unless a product-specific evaluation proves coverage.','Validate ontology URI handling, APIs, version history, workflow controls and integration architecture. [S23-S25]'),
]
add_table(doc,['Option','Business vocabulary','Propagation and workflow','Recommended role','Diligence focus'],rows,widths=[0.7,1.55,1.75,1.55,1.65],font_size=7.35)
add_heading(doc,'7.2 Ontology workbench and runtime options',2)
rows=[
('Protégé / WebProtégé','Open-source ontology editing and collaborative modeling.','Domain model authoring, workshops, review and learning. [S6]'),
('TopBraid EDG','Ontology-centered governance environment optimized for SHACL-defined graph models.','Ontology-intensive enterprise stewardship when a dedicated semantic workbench is justified. [S12]'),
('Stardog','Enterprise knowledge graph platform built on RDF standards with SPARQL, GraphQL and SHACL constraints.','Managed or enterprise knowledge graph runtime with validation and query needs. [S13]'),
('GraphDB','RDF database with standard rulesets for RDFS, OWL-Horst, OWL2-RL and OWL2-QL, plus custom rulesets.','Runtime when configurable reasoning and graph operations are central. [S14]'),
('Apache Jena / Fuseki','Open-source Java RDF framework and SPARQL server.','Composable engineering stack where a team owns operations. [S7]'),
('Eclipse RDF4J','Java RDF framework with repository APIs and SHACL capabilities.','Composable Java-centric integration and runtime. [S10]'),
('RDFLib + pySHACL','Python RDF processing and SHACL validation.','Starter kit, CI, ETL and service integration. [S8-S9]'),
('Ontop','Virtual knowledge graph / ontology-based data access approach.','Expose relational data through semantic mappings without copying all source data into a graph. [S11]'),
]
add_table(doc,['Option','What it is','When to shortlist'],rows,widths=[1.25,2.7,3.45],font_size=7.9)
add_heading(doc,'7.3 Weighted procurement scorecard',2)
rows=[
('Stewardship UX and workflow',25,'Can domain stewards propose, review, approve, deprecate and audit terms without engineering support?'),
('APIs, events and automation',20,'Can releases, diffs, workflow events and mappings be integrated into CI/CD and agent tooling?'),
('Lineage and metadata propagation',15,'Can approved meaning move to related assets with scope, direction and audit controls?'),
('Standards portability',15,'Can you export stable URIs, RDF/SKOS/OWL/SHACL or equivalent portable representations without lock-in?'),
('AI context integration',10,'Can agents retrieve approved context bundles with version, policy and provenance?'),
('Operations and total cost',10,'What skills, infrastructure, support and upgrade burden are required?'),
('Ecosystem fit',5,'How well does the option integrate with your warehouse, semantic layer, BI, IAM, ticketing and observability stack?'),
]
add_table(doc,['Criterion','Weight','Evaluation question'],rows,widths=[2.05,0.65,4.7],font_size=8.1)
add_heading(doc,'7.4 Scenario recommendations',2)
add_bullet(doc,'Fastest managed catalog adoption: shortlist Atlan and Alation for the collaboration layer, then pair the chosen catalog with a portable RDF/SKOS/SHACL registry and a runtime only where necessary.')
add_bullet(doc,'Open-source and API-first control: shortlist OpenMetadata as the catalog, Git plus Protégé for the registry workflow, RDFLib plus pySHACL for CI, and Jena/Fuseki, RDF4J or GraphDB for runtime requirements.')
add_bullet(doc,'Ontology-intensive or regulated domains: shortlist TopBraid EDG for semantic stewardship and Stardog or GraphDB for graph-runtime needs; integrate the enterprise catalog so definitions remain discoverable to non-specialists.')
add_bullet(doc,'Virtualization-heavy architecture: evaluate Ontop when relational sources should remain authoritative and semantic mappings should expose a virtual graph.')
add_callout(doc,'Do not skip the proof of value','Run the same 25 to 75 concepts, approval workflow, catalog sync, lineage impact scenario and agent context retrieval through each shortlisted stack. Score the operating experience, not the product demo.',fill=LIGHT_TEAL,accent=TEAL)

# Section 8
new_page(doc)
add_heading(doc,'8. Scale through an operating model',1)
add_heading(doc,'8.1 Use clear accountability',2)
rows=[
('Executive sponsor','Select the business outcome, remove cross-domain blockers and hold teams accountable for adoption.'),
('Domain council','Approve high-impact definitions, resolve conflicts and prioritize expansion.'),
('Ontology steward','Curate concepts, review proposals, enforce URI discipline and manage releases.'),
('Data product owner','Map concepts to physical and semantic implementations; maintain quality evidence.'),
('Platform team','Operate registry, validation, catalog adapters, graph runtime, CI/CD and context APIs.'),
('AI product owner','Consume approved context, log versions, monitor failure signals and submit refresh proposals.'),
]
add_table(doc,['Role','Accountability'],rows,widths=[1.6,5.8],font_size=8.4)
add_heading(doc,'8.2 Use a release workflow',2)
for step in [
'Discover: collect candidate concepts and changes from domain workshops, lineage drift, schema drift, usage data, search logs, quality incidents and AI observability.',
'Propose: create a structured change proposal with source evidence, affected concepts, mappings and rationale.',
'Validate: run SHACL checks, competency queries, reconciliation tests and semantic regression tests.',
'Review: assign domain steward and data-product owner approval; require security, privacy or finance approval when the concept crosses control boundaries.',
'Release: issue a versioned ontology release with effective date, provenance and change summary.',
'Propagate: update runtime, catalog, semantic layer documentation, agent context indexes and impacted consumers.',
'Measure: track adoption, freshness, answer quality, change safety and business outcomes.'
]: add_number(doc,step)
add_heading(doc,'8.3 A 12-week adoption plan',2)
rows=[
('Weeks 1-2','Select one use case, 25 to 75 concepts, competency questions, stewards and success metrics.','Charter and prioritized concept backlog.'),
('Weeks 3-4','Model SKOS vocabulary, URI rules, minimum governance metadata and 5 to 10 critical relationships.','Ontology release 0.1 in Git and reviewed definitions.'),
('Weeks 5-6','Add asset mappings, metric logic, SHACL controls and CI validation.','Publishable release gate and test evidence.'),
('Weeks 7-8','Synchronize glossary objects into the catalog; route proposals and approvals through the chosen workflow.','Catalog-visible meaning and stewardship workflow.'),
('Weeks 9-10','Expose context API/tool to one AI application and one analytics workflow; log context versions.','First runtime consumers and evaluation set.'),
('Weeks 11-12','Connect refresh signals, measure KPIs, document decisions and prioritize the next domain.','Operating cadence and expansion plan.'),
]
add_table(doc,['Timing','Focus','Exit evidence'],rows,widths=[1.0,4.0,2.4],font_size=8.25)
add_heading(doc,'8.4 Business-value flywheels',2)
rows=[
('Metric trust flywheel','Approved definitions -> mapped semantic models -> fewer reconciliations -> higher reuse -> better prioritization of definitions.'),
('Agent reliability flywheel','Approved context retrieval -> fewer hallucinated definitions -> logged misses -> new proposals -> better context coverage.'),
('Change-safety flywheel','Lineage impact analysis -> targeted testing -> safer releases -> more adoption -> richer lineage evidence.'),
('Stewardship productivity flywheel','AI-assisted draft proposals -> faster human review -> more catalog coverage -> better discovery signals -> higher-quality proposals.'),
]
add_table(doc,['Flywheel','Value loop'],rows,widths=[1.75,5.65],font_size=8.4)

# Section 9
new_page(doc)
add_heading(doc,'9. Production hardening checklist',1)
checks=[
('Scope','One funded use case, bounded concept backlog and named business outcome.'),
('Identity','Controlled URI namespace, stable identifiers, alias strategy and deprecation policy.'),
('Governance','Stewards, reviewers, escalation path, release cadence and control-boundary approvals.'),
('Modeling','SKOS vocabulary, selected OWL rules only where useful, and documented competency questions.'),
('Validation','SHACL shapes, SPARQL regression queries, metric reconciliation tests and agent evaluation set.'),
('Provenance','Proposal source, reviewer, approval, effective date, release ID and rollback path.'),
('Catalog sync','Idempotent adapter, dry-run diff, write controls, catalog-ID persistence and failure handling.'),
('Runtime','Context API authentication, cache invalidation, rate limits, observability and approved-version enforcement.'),
('Refresh','Schema drift, lineage drift, usage, search and AI signals connected to proposal creation.'),
('Metrics','Trust, freshness, reuse, answer quality, change safety and onboarding-time KPIs reviewed monthly.'),
('Portability','Export tested so concepts and identifiers are not trapped inside a single vendor implementation.'),
('Security','Sensitive definitions, policies, context bundles and approval actions protected by least privilege.'),
]
add_table(doc,['Area','Ready-for-scale evidence'],checks,widths=[1.25,6.15],font_size=8.45)
add_heading(doc,'9.1 Immediate next actions',2)
for item in [
'Choose one bounded business use case and identify 25 to 75 high-value concepts.',
'Run the included starter kit and replace the example vocabulary with 5 to 10 real concepts.',
'Create a SHACL rule for each governance failure you cannot allow into production.',
'Shortlist a catalog-layer option and a registry/runtime pattern separately.',
'Complete a proof of value that includes approval, propagation, impact analysis and agent context retrieval.',
'Fund a monthly domain stewardship cadence before expanding the ontology surface area.'
]: add_number(doc,item)
add_callout(doc,'Practical conclusion','A living ontology is not a one-time modeling exercise. It is a governed product with a release pipeline, business owners, tests, catalog propagation, runtime consumers and measurable feedback loops. AI is most useful when it accelerates this product lifecycle rather than replacing it.',fill=LIGHT_BLUE,accent=BLUE)

# Appendix
new_page(doc)
add_heading(doc,'Appendix A. Starter-kit inventory',1)
rows=[
('ontology/enterprise_ai.ttl','Reference ontology and governed SKOS vocabulary.'),
('ontology/shapes.ttl','SHACL publication controls.'),
('data/sample_data_valid.ttl','Passing mapped-asset sample.'),
('data/sample_data_invalid.ttl','Intentionally weak sample for CI demonstration.'),
('src/validate_graph.py','SHACL validation entry point.'),
('src/query_context.py','Approved-context retrieval example.'),
('src/propose_refresh.py','Overdue-review refresh proposal generator.'),
('src/export_catalog_glossary.py','Canonical CSV glossary export.'),
('src/sync_openmetadata.py','Dry-run OpenMetadata payload generator; review against tenant version before writes.'),
('src/sync_atlan.py','Atlan import CSV generator; adapt to tenant import template or pyatlan SDK.'),
('src/context_api.py','Minimal FastAPI context endpoint.'),
('.github/workflows/ontology-ci.yml','CI publication gate.'),
('screenshots/','Original tutorial illustrations and execution screenshots used in this guide.'),
]
add_table(doc,['File','Purpose'],rows,widths=[2.45,4.95],font_size=8.25)
add_heading(doc,'Appendix B. Official sources reviewed',1)
sources=[
('S1','W3C RDF 1.1 Primer','https://www.w3.org/TR/rdf11-primer/'),
('S2','W3C SKOS Simple Knowledge Organization System Reference','https://www.w3.org/TR/skos-reference/'),
('S3','W3C OWL 2 Web Ontology Language Document Overview','https://www.w3.org/TR/owl2-overview/'),
('S4','W3C Shapes Constraint Language (SHACL)','https://www.w3.org/TR/shacl/'),
('S5','W3C PROV-O: The PROV Ontology','https://www.w3.org/TR/prov-o/'),
('S6','Protégé ontology editor','https://protege.stanford.edu/'),
('S7','Apache Jena documentation','https://jena.apache.org/documentation/'),
('S8','RDFLib documentation','https://rdflib.readthedocs.io/'),
('S9','pySHACL','https://github.com/RDFLib/pySHACL'),
('S10','Eclipse RDF4J documentation','https://rdf4j.org/documentation/'),
('S11','Ontop documentation','https://ontop-vkg.org/'),
('S12','TopBraid EDG: Working with ontologies','https://www.topquadrant.com/doc/8.5/user_guide/guidance_specific_to_asset_collection_type/working_with_ontologies/working_with_ontologies.html'),
('S13','Stardog enterprise knowledge graph platform','https://www.stardog.com/platform/'),
('S14','GraphDB inferencing documentation','https://graphdb.ontotext.com/documentation/11.3/inference.html'),
('S15','Atlan documentation: A Business Graph','https://docs.atlan.com/product/capabilities/governance/glossary/concepts/what-is-a-glossary'),
('S16','Atlan documentation: Lineage','https://docs.atlan.com/product/capabilities/lineage'),
('S17','Atlan documentation: Metadata Propagator','https://docs.atlan.com/product/capabilities/lineage/references/metadata-propagator'),
('S18','Atlan documentation: Set up playbooks','https://docs.atlan.com/product/capabilities/playbooks/how-tos/set-up-playbooks'),
('S19','OpenMetadata documentation: Metadata Standard','https://docs.open-metadata.org/v1.12.x/api-reference/main-concepts/metadata-standard'),
('S20','OpenMetadata documentation: Glossary','https://docs.open-metadata.org/v1.12.x/how-to-guides/data-governance/glossary'),
('S21','OpenMetadata documentation: Lineage','https://docs.open-metadata.org/v1.12.x/api-reference/lineage'),
('S22','OpenMetadata documentation: Glossary Approval Workflow','https://docs.open-metadata.org/v1.12.x/how-to-guides/data-governance/workflows/default-workflows/glossary-approval'),
('S23','Alation: Data Catalog','https://www.alation.com/product/data-catalog/'),
('S24','Alation: Business Glossary at Scale','https://www.alation.com/blog/enterprise-data-glossary-management/'),
('S25','Alation: Workflow Automation','https://www.alation.com/product/workflow-automation/'),
]
add_table(doc,['Ref','Source','URL'],sources,widths=[0.55,3.0,3.85],font_size=7.35)
add_para(doc,'Vendor capabilities change over time and may differ by edition, tenant configuration and release. Confirm requirements through a tenant-specific proof of value before procurement or production architecture decisions.',space_before=4,space_after=3)
add_para(doc,'All diagrams, code screenshots, terminal screenshots and catalog mockups in this guide are original tutorial assets generated for the included starter kit. They are not screenshots of Atlan, OpenMetadata, Alation, Protégé, TopBraid, Stardog or GraphDB user interfaces.',space_after=1)

# Final formatting: prevent orphan headings and set table widths where possible
for p in doc.paragraphs:
    if p.style.name.startswith('Heading'):
        p.paragraph_format.keep_with_next=True

# save
doc.save(OUT)
print(OUT)
