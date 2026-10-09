"""Independent Study 7 public arithmetic and source verifier; Python standard library only."""
import argparse
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

ENGINES = ['ChatGPT','Claude','Perplexity','Google AI Overviews','Google AI Mode']
STATES = ['stated_on_read_page','not_stated_on_read_page','unknown_unread_page']
REVIEW = 'Team review: in progress'

def digest(text):
    return hashlib.sha256(text.encode('utf8')).hexdigest()

def identity(row):
    return '|'.join(str(row[k]) for k in ['category_id','question_id','engine','repeat_index'])

def rate(count,base):
    if not base:
        return dict(count=count,base=base,rate=None,lower=None,upper=None)
    z=1.959963984540054
    p=count/base
    denominator=1+z*z/base
    center=(p+z*z/(2*base))/denominator
    half=z*math.sqrt(p*(1-p)/base+z*z/(4*base*base))/denominator
    return dict(count=count,base=base,rate=round(p*100,1),lower=round(100*max(0,center-half),1),upper=round(100*min(1,center+half),1))

def sources(rows):
    per_answer=defaultdict(set)
    for row in rows:
        per_answer[row['record_id']].update(row['sources'])
    found=defaultdict(set)
    for rid,urls in per_answer.items():
        for url in urls or {'no source shown'}:
            found[url].add(rid)
    return [dict(source=url,answer_count=len(ids),record_ids=sorted(ids)) for url,ids in sorted(found.items())]

def verify(data, answers_path=None, release_path=None):
    errors=[]
    def check(test,message):
        if not test:
            errors.append(message)
    def unique(rows,key,label):
        check(len({r[key] for r in rows})==len(rows),label+' duplicate identifiers')
    def reviewed(row,label):
        check(row.get('review_status')==REVIEW and row.get('verified') is False,label+' review status')
    check(data.get('schema_version')=='study7-index-2','schema version')
    check(data['publication']['state'] in ['draft','ready_for_deposit'],'publication state')
    if data['publication']['state']=='ready_for_deposit':
        check(data['publication']['gate_ready'] is True and data['publication']['gate_error_count']==0 and not data['publication']['gate_blockers'],'publication gate')
    check(data['publication']['verified_criteria']==0,'verified count')
    check(data['study']['byline']=='Prepared by the Broadcastwell team','byline')
    check(data['source']['engines']==ENGINES,'engine names')
    check(data['source']['capture_dates']==['2026-09-22','2026-09-23'],'source dates')
    check(data['source']['doi']=='10.5281/zenodo.22907695','source DOI')
    check(data['source']['answers_asset']==dict(url='https://zenodo.org/api/records/22907695/files/answers-2026-09.jsonl/content',sha256='221c94e1ebad2bc87d7cd20837fa670cc40b10dba6f68b75423dc8bee69697b3'),'deposited answer identity')
    check(data['source']['release_asset']==dict(url='https://zenodo.org/api/records/22907695/files/release-2026-09.json/content',sha256='e7829183f6785357787fcf85d3c27999403b0a329f349dad4c7343b11d23f142'),'deposited release identity')
    raw=None
    frozen=None
    if release_path:
        b=Path(release_path).read_bytes()
        check(hashlib.sha256(b).hexdigest()==data['source']['release_asset']['sha256'],'public release asset hash')
        frozen={c['id']:c for c in json.loads(b)['categories']}
    if answers_path:
        b=Path(answers_path).read_bytes()
        check(hashlib.sha256(b).hexdigest()==data['source']['answers_asset']['sha256'],'public answer asset hash')
        rows=[json.loads(line) for line in b.decode('utf8').splitlines()]
        raw={identity(r):r for r in rows}
        check(len(rows)==len(raw)==2250,'deposited source record identity coverage')
        check(all(r.get('dedup_key',identity(r))==identity(r) for r in rows),'deposited source identity derivation')
    unique(data['categories'],'id','categories')
    check(len(data['categories'])==14,'fourteen categories')
    totals=dict(scheduled_answers=0,original_exclusions=0,eligible_inputs=0,derived_exclusions=0,answer_base=0)
    exclusions=[]
    for cat in data['categories']:
        cid=cat['id']
        reviewed(cat,cid)
        if frozen is not None:
            original=frozen[cid]
            top=sorted(original['vendors'],key=lambda v:(-v['mention_rate']['count'],v['name']))[:5]
            check(cat['name']==original['name'] and cat['questions']==[{k:q[k] for k in ['id','text']} for q in original['questions']],cid+' original category and questions')
            check(cat['comparison_vendors']==[v['name'] for v in top],cid+' original median population')
            check(cat['comparison_vendor_aliases']=={v['name']:[v['name'],*v.get('aliases',[])] for v in top},cid+' original vendor aliases')
        unique(cat['records'],'record_id',cid+' records')
        unique(cat['criteria'],'id',cid+' criteria')
        records={r['record_id']:r for r in cat['records']}
        questions=[q['id'] for q in cat['questions']]
        scheduled={f'{cid}|{q}|{engine}|{run}' for q in questions for engine in ENGINES for run in [1,2,3]}
        check(set(records)==scheduled,cid+' scheduled source coverage')
        check(len(questions)==10 and len(set(questions))==10,cid+' question count')
        base=sum(r['included'] for r in records.values())
        check(base==cat['answer_base'],cid+' answer base')
        original=sum(r['exclusion_stage']=='original' for r in records.values())
        derived=sum(r['exclusion_stage']=='study' for r in records.values())
        check(cat['input_answers']==len(records)-original,cid+' eligible input base')
        check(cat['scheduled_answers']==len(records),cid+' scheduled base')
        totals['scheduled_answers']+=len(records)
        totals['original_exclusions']+=original
        totals['eligible_inputs']+=len(records)-original
        totals['derived_exclusions']+=derived
        totals['answer_base']+=base
        for rid,r in records.items():
            check(rid==f"{cid}|{r['question_id']}|{r['engine']}|{r['run']}",cid+' record identity')
            check(r['included']==(r['exclusion_stage'] is None),rid+' inclusion flag')
            check(r['captured_at'][:10] in data['source']['capture_dates'],rid+' date')
            if r['exclusion_stage']:
                check(bool(r['exclusion_reason']),rid+' exclusion reason')
                exclusions.append(dict(category_id=cid,record_id=rid,stage=r['exclusion_stage'],reason=r['exclusion_reason'],reason_display=r['exclusion_reason_display']))
            if raw is not None:
                source=raw.get(rid)
                check(source is not None,rid+' source exists')
                if source:
                    check(digest(source['answer_text'])==r['answer_sha256'],rid+' answer hash')
                    check(source['captured_at']==r['captured_at'] and source['cited_urls']==r['cited_urls'],rid+' source attribution')
                    check(source['excluded']==(r['exclusion_stage']=='original'),rid+' original exclusion')
        criteria={r['id']:r for r in cat['criteria']}
        evidence={r['id']:r for r in cat['evidence']}
        unique(cat['evidence'],'id',cid+' evidence')
        unique(cat['adjacency'],'id',cid+' adjacency')
        for kind in ['evidence','adjacency']:
            for e in cat[kind]:
                tag=cid+'/'+e['id']
                reviewed(e,tag)
                record=records.get(e['record_id'])
                check(record is not None and record['included'],tag+' valid source')
                check(e['criterion_id'] in criteria,tag+' criterion')
                check(type(e['start']) is int and type(e['end']) is int and 0<=e['start']<e['end'],tag+' offsets')
                check(e['offset_unit']=='Unicode code points',tag+' offset unit')
                if record:
                    check(all(e[k]==record[k] for k in ['engine','question_id','run','captured_at','answer_sha256']),tag+' attribution')
                if kind=='evidence':
                    check(e['end']<=e['first_vendor_offset'] and e['first_vendor_offset']==record['first_vendor_offset'],tag+' prefix boundary')
                else:
                    check(any(x['record_id']==e['record_id'] and x['criterion_id']==e['criterion_id'] for x in cat['evidence']),tag+' adjacent prefix requirement')
                    matches=[name for name,aliases in cat['comparison_vendor_aliases'].items() if e['vendor_normalized'].casefold() in [a.casefold() for a in aliases]]
                    check(e['comparison_vendor']==(matches[0] if len(matches)==1 else None),tag+' comparison identity')
                if e['engine']=='Perplexity':
                    check('quote' not in e,tag+' Perplexity quotation must be absent')
                else:
                    check(isinstance(e.get('quote'),str) and digest(e['quote'])==e['quote_sha256'],tag+' exact quotation hash')
                    check(len(e.get('quote',''))==e['end']-e['start'],tag+' quotation length')
                check(e['source_doi']==data['source']['doi'] and e['source_asset_url']==data['source']['answers_asset']['url'],tag+' source reference')
                if raw is not None and e['record_id'] in raw:
                    source=raw[e['record_id']]['answer_text']
                    exact=source[e['start']:e['end']]
                    check(digest(exact)==e['quote_sha256'] and ('quote' not in e or e['quote']==exact),tag+' source offsets and quotation')
                    if kind=='adjacency':
                        check(e['vendor_as_named'] in exact,tag+' adjacent vendor spelling')
        for criterion in cat['criteria']:
            key=criterion['id'];tag=cid+'/'+key
            reviewed(criterion,tag)
            spans=[e for e in cat['evidence'] if e['criterion_id']==key]
            ids=sorted({e['record_id'] for e in spans})
            check(criterion['record_ids']==ids,tag+' record count inputs')
            check(criterion['evidence_ids']==[e['id'] for e in spans],tag+' evidence coverage')
            check(criterion['frequency']==rate(len(ids),base),tag+' count and Wilson interval')
            check(criterion['source_counts']==sources(spans),tag+' source counts')
            expected=[]
            for engine in ENGINES:
                for question in questions:
                    runs=sorted({records[rid]['run'] for rid in ids if records[rid]['engine']==engine and str(records[rid]['question_id'])==str(question)})
                    expected.append(dict(engine=engine,question_id=question,stated_in_n_of_3=len(runs),runs=runs,scheduled_runs=3))
            check(criterion['repeat_confidence']==expected,tag+' n of 3 repeats')
            events=[e for e in cat['adjacency'] if e['criterion_id']==key]
            names=sorted({e['vendor_normalized'] for e in events})
            check([v['vendor'] for v in criterion['adjacent_vendors']]==names,tag+' adjacent vendor coverage')
            med=statistics.median([len({e['record_id'] for e in events if e['comparison_vendor']==name}) for name in cat['comparison_vendors']])
            for vendor in criterion['adjacent_vendors']:
                matches=[e for e in events if e['vendor_normalized']==vendor['vendor']]
                rids=sorted({e['record_id'] for e in matches})
                check(vendor['record_ids']==rids and vendor['evidence_ids']==[e['id'] for e in matches],tag+' adjacency source inputs')
                check(vendor['frequency']==rate(len(rids),base) and vendor['named_beside_in_two_or_more']==(len(rids)>=2),tag+' adjacency frequency')
                expected_sources=sources(matches)
                source_panel={name:{s['source']:s['answer_count'] for s in sources([e for e in events if e['comparison_vendor']==name])} for name in cat['comparison_vendors']}
                for source in expected_sources:
                    source_med=statistics.median([source_panel[name].get(source['source'],0) for name in cat['comparison_vendors']])
                    source.update(frequency=rate(source['answer_count'],base),category_median_count=source_med,category_median_base=base,category_median_rate=round(100*source_med/base,1),median_population=cat['comparison_vendors'])
                check(vendor['source_counts']==expected_sources,tag+' adjacency sources and source medians')
                check(vendor['category_median_count']==med and vendor['category_median_base']==base and vendor['category_median_rate']==round(100*med/base,1) and vendor['median_population']==cat['comparison_vendors'],tag+' adjacency median')
        panel=cat['comparison_vendors']
        check(len(panel)==len(set(panel))==5,cid+' five vendor comparison population')
        pairs=[(p['vendor'],p['criterion_id']) for p in cat['vendor_pages']]
        check(len(pairs)==len(set(pairs)) and set(pairs)=={(v,key) for v in panel for key in criteria},cid+' full page comparison coverage')
        for p in cat['vendor_pages']:
            tag=cid+'/'+p['vendor']+'/'+p['criterion_id']
            reviewed(p,tag)
            check(p['state'] in STATES,tag+' page state')
            check(p['canonical']==criteria[p['criterion_id']]['canonical'],tag+' page criterion')
            check(bool(p['scope']) and bool(p['page_read_utc']) and len(p['page_sha256'])==64 and len(p['page_text_sha256'])==64,tag+' dated page provenance')
            check(bool(p['evidence'])==(p['state']=='stated_on_read_page'),tag+' page evidence state')
            check(not p['scope_unusable_reason'] or p['state']=='unknown_unread_page',tag+' unknown partial scope')
            for e in p['evidence']:
                check(digest(e['quote'])==e['quote_sha256'] and len(e['quote'])==e['end']-e['start'] and e['start']>=0,tag+' page quotation hash')
        check([v['vendor'] for v in cat['vendor_summaries']]==panel,cid+' page summary coverage')
        for vendor in cat['vendor_summaries']:
            reviewed(vendor,cid+'/'+vendor['vendor'])
            check(vendor['median_population']==panel,cid+' page median population')
            for state in STATES:
                counts=[sum(p['vendor']==v and p['state']==state for p in cat['vendor_pages']) for v in panel]
                med=statistics.median(counts);count=counts[panel.index(vendor['vendor'])];denom=len(criteria)
                expected=dict(**rate(count,denom),category_median_count=med,category_median_base=denom,category_median_rate=round(100*med/denom,1))
                check(vendor['metrics'][state]==expected,cid+' page metric and median')
    check(all(data['population'][k]==v for k,v in totals.items()),'population totals')
    check(data['population']['exclusions']==exclusions,'population exclusion records')
    check(totals==dict(scheduled_answers=2100,original_exclusions=5,eligible_inputs=2095,derived_exclusions=2,answer_base=2093),'frozen population definitions')
    return errors

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('publication',type=Path)
    ap.add_argument('--answers-source',type=Path,help='Downloaded deposited answers JSONL; optional exact hash and offset verification')
    ap.add_argument('--release-source',type=Path,help='Downloaded deposited release JSON; optional median population and alias verification')
    args=ap.parse_args()
    try:
        errors=verify(json.loads(args.publication.read_text(encoding='utf8')),args.answers_source,args.release_source)
    except (KeyError,TypeError,ValueError) as exc:
        errors=['Malformed public contract: '+str(exc)]
    print(json.dumps(dict(valid=not errors,errors=errors,source_answers_checked=bool(args.answers_source),source_release_checked=bool(args.release_source)),indent=2))
    raise SystemExit(1 if errors else 0)

if __name__=='__main__':
    main()
