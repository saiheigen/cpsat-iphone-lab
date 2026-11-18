#!/usr/bin/env python3
"""Synthetic-only, zero-egress Linux WebKit Worker-origin diagnostics.
Not a solver test, not iOS Safari. Every HTTPS navigation is fulfilled locally.
"""
import json
from pathlib import Path
import tempfile
from playwright.sync_api import sync_playwright

HTML="""<!doctype html><meta charset="utf-8"><title>Local Worker Probe</title>
<main>Only synthetic test bytes: no roster, no remote resources.</main>"""
JS=r"""async () => {
  const state={origin:location.origin,url_protocol:location.protocol,
    secure_context:isSecureContext,worker_available:typeof Worker==="function",
    blob_url_available:typeof URL.createObjectURL==="function"};
  if(!state.worker_available||!state.blob_url_available)
    return {...state,worker:"unavailable"};
  return new Promise(resolve=>{
    let finished=false,w=null,url=null;
    const complete=(kind,extra={})=>{
      if(finished)return;finished=true;
      if(w)w.terminate();
      if(url)URL.revokeObjectURL(url);
      resolve({...state,worker:kind,...extra});
    };
    try {
      url=URL.createObjectURL(new Blob([
        'self.postMessage({type:"ready",answer:42})'
      ],{type:"text/javascript"}));
      w=new Worker(url);
      w.onmessage=event=>complete("ready",{message:event.data});
      w.onerror=event=>complete("error",{message:event.message||"unknown worker error",
                                            filename:event.filename||""});
      setTimeout(()=>complete("timeout"),6000);
    } catch(e){complete("throw",{message:String(e)})}
  });
}"""

def probe(browser,mobile,method):
    ctx=browser.new_context(viewport={"width":390,"height":844} if mobile
                            else {"width":1280,"height":800},
                            offline=True,is_mobile=mobile,has_touch=mobile)
    page=ctx.new_page()
    requests=[]
    page.on("request",lambda request: requests.append(request.url))
    record={"engine":"linux-webkit","mobile_emulation":mobile,
            "load_method":method,"real_iphone_safari":False,
            "actual_network_egress":False}
    try:
        if method=="about_blank":
            page.goto("about:blank")
            page.set_content(HTML,wait_until="domcontentloaded")
        elif method=="local_fulfilled_https":
            target="https://synthetic-worker-probe.invalid/offline.html"
            def onroute(route):
                if route.request.url!=target:
                    raise AssertionError("Unexpected external request: "+route.request.url)
                route.fulfill(status=200,content_type="text/html; charset=utf-8",body=HTML)
            ctx.route("**/*",onroute)
            page.goto(target,wait_until="domcontentloaded",timeout=15000)
        elif method=="file":
            with tempfile.TemporaryDirectory() as td:
                file=Path(td)/"index.html"
                file.write_text(HTML,encoding="utf-8")
                page.goto(file.as_uri(),wait_until="domcontentloaded",timeout=15000)
        record.update(page.evaluate(JS))
    except Exception as e:
        record.update({"worker":"navigation_or_eval_error",
                       "error":str(e).splitlines()[0][:350]})
    finally:
        record["intercepted_urls"]=requests
        ctx.close()
    return record

def main():
    with sync_playwright() as playwright:
        browser=playwright.webkit.launch(headless=True)
        try:
            data=[probe(browser,mobile,method)
                  for mobile in (False,True)
                  for method in ("about_blank","local_fulfilled_https","file")]
        finally:browser.close()
    result={"passed_any_worker":any(r["worker"]=="ready" for r in data),
            "real_iphone_safari_tested":False,"records":data}
    Path("phase5_webkit_worker_origin_probe.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))
    # A diagnostic outcome is not a product acceptance decision.
if __name__=="__main__":main()
