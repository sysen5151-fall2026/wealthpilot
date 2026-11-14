"""Local-only Chapter 10 instrumentation around the unchanged public API.
Use the copied project. Never deploy these experiment endpoints publicly.
"""
import sys,time,json,functools,contextvars,random,hashlib,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
import uvicorn
import wealthpilot_service.pipeline as pipeline
from wealthpilot_service.api import create_app
from investor_interface.console import SAMPLE_INVESTOR
from ch10_measure import STAGES,identity
from market_data_provider.snapshot_cache import VerifiedSnapshotCache
OUT=Path(os.environ.get('CH10_OUT','evidence/ch10/revision/browser_holdout'));OUT.mkdir(parents=True,exist_ok=True)
META=identity()
ctx=contextvars.ContextVar('ch10',default=None);records=[];client=[];originals={n:getattr(pipeline,n) for n in STAGES}
snapshot=Path(pipeline.DEFAULT_SNAPSHOT_DIRECTORY);manifest=json.loads((snapshot/'manifest.json').read_text())
def observe(stage,start,end):
 c=ctx.get()
 if c is not None:c['stages'].append({'stage':stage,'entry_ns':start,'exit_ns':end})
cache=VerifiedSnapshotCache(observe)

def wrap(name,fn):
 @functools.wraps(fn)
 def inner(*args,**kwargs):
  c=ctx.get();t=time.perf_counter_ns()
  try:
   if name=='provide_historical_market_data' and c and c['scenario']=='cached':
    if (int(c['run'])-1)%10==0:cache.invalidate()
    return cache(*args,**kwargs)
   return fn(*args,**kwargs)
  finally:
   if c is not None:c['stages'].append({'stage':STAGES[name],'entry_ns':t,'exit_ns':time.perf_counter_ns()})
 return inner
for n,fn in originals.items():setattr(pipeline,n,wrap(n,fn))
planner=pipeline.Planner(database_path=OUT/'browser.sqlite');product=create_app(planner)
app=FastAPI();order=['baseline','cached']*100;random.Random(5151).shuffle(order)
@app.get('/ch10/fixture')
def fixture():return {'fixture':SAMPLE_INVESTOR,'order':order,'cache_workload':'90 percent hits; deliberate eviction each 10 requests; prepare included on miss'}
@app.post('/ch10/records')
async def record(request:Request):
 data=await request.json();client.append(data)
 (OUT/'browser_measurements.json').write_text(json.dumps({'meta':{**META,'cache_workload':'90 percent hits; deliberate eviction each 10 requests; prepare included on miss','snapshot':manifest,'workload':'fixed synthetic fixture; 100 each, randomized interleaving seed 5151; actual frontend and HTTP over loopback','display_metric':'two requestAnimationFrame callbacks after DOM update; display opportunity proxy, not physical screen instrumentation'},'client':client,'server':records},indent=2))
 return {'received':len(client)}
@app.get('/ch10/status')
def status():return {'client_runs':len(client),'server_requests':len(records)}
class Timing:
 def __init__(self,app):self.app=app
 async def __call__(self,scope,receive,send):
  if scope['type']!='http' or not scope['path'].startswith('/api/'):
   await self.app(scope,receive,send);return
  headers=dict(scope.get('headers',[]));c={'scenario':headers.get(b'x-ch10-scenario',b'baseline').decode(),'run':headers.get(b'x-ch10-run',b'0').decode(),'path':scope['path'],'entry_ns':time.perf_counter_ns(),'stages':[]};token=ctx.set(c)
  async def measured_send(message):
   if message['type']=='http.response.start':c['status']=message['status'];c['headers_ns']=time.perf_counter_ns()
   await send(message)
   if message['type']=='http.response.body' and not message.get('more_body',False):c['exit_ns']=time.perf_counter_ns()
  try:await self.app(scope,receive,measured_send)
  finally:
   c.setdefault('exit_ns',time.perf_counter_ns());records.append(c);ctx.reset(token)
app.add_middleware(Timing);app.mount('/',product)
if __name__=='__main__':uvicorn.run(app,host='127.0.0.1',port=8766,log_level='warning')
