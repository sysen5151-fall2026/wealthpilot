"""Render a local N-01 review form; never fill in review decisions."""
import html
import json


def render_n01(packet, path):
    cases = []
    for i, case in enumerate(packet["cases"]):
        cases.append(f'''<section><h2>{case['case_id']}</h2>
        <h3>输入资料（虚拟案例）</h3><pre>{html.escape(json.dumps(case['synthetic_input'],indent=2))}</pre>
        <h3>实际计划输出</h3><pre>{html.escape(case['display_text'])}</pre>
        <label>独立判断：目标、期限、资金能力、已有持仓是否全部一致？
        <select id="decision-{i}" required><option value="">尚未复核</option value="true">四项全部一致</option value="false">至少一项不一致</option></select></label>
        <label>依据或不一致之处（必填）<textarea id="notes-{i}" required></textarea></label></section>''')
    payload = json.dumps(packet).replace("</", "<\\/")
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>N01 独立复核表</title>
    <style>body{background:#f4f5f6;color:#17232e;font:17px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;margin:0}main{max-width:930px;margin:auto;padding:40px 28px}section{margin-top:40px;padding-top:20px;border-top:1px solid #c6cdd3}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#fff;padding:20px;font-size:14px}label{display:block;margin:16px 0}input,select,textarea{display:block;font:inherit;padding:9px;border:1px solid #9daab5;border-radius:4px;width:95%}input[type=checkbox]{display:inline;width:auto}textarea{min-height:90px}button{background:#24577c;color:#fff;font:inherit;padding:12px 20px;border:0;border-radius:6px}#message{font-weight:bold}</style><main>
    <h1>N-01 十组案例独立复核</h1>
    <p>这不是自动通过按钮。请由未编写该实现的独立复核人，逐组比较输入与计划输出，记录真实判断。自动检查已有 10/10 一致，但不代替你的复核。所有判断默认留空。</p>
    <p>核对四项：目标是否一致；期限是否一致；资金及每月投入是否正确；持仓与总额是否正确。还应检查解释是否与输入矛盾。至少 9/10 通过才达到原 N-01 标准。</p>
    <p>本表只在本机处理，不发送到外部服务。关闭或刷新前请先导出，未导出的输入不会自动保存。</p>
    <label>真实复核人编号（可用化名）<input id="reviewer" required></label>
    <label>实际复核日期<input id="date" type="date" required></label>
    <label><input id="independent" type="checkbox"> 我确认我是独立复核人，已实际完成下列检查。</label>
    '''+"".join(cases)+'''
    <p id="message"></p><button id="export">导出真实复核记录</button>
    <p>下载后，将 JSON 放回项目 evidence/acceptance 文件夹，替换同名 n01-independent-review-packet.json，再运行 N-01 测试。原始案例、输入和输出不能修改；测试会重新生成并核对基线。</p>
    </main><script>
    const packet=PACKET;
    document.getElementById('export').onclick=()=>{
      const reviewer=document.getElementById('reviewer').value.trim();
      const day=document.getElementById('date').value;
      const independent=document.getElementById('independent').checked;
      if(!reviewer||!day||!independent){alert('请填写真实复核人、日期，并确认独立复核。');return;}
      for(let i=0;i<packet.cases.length;i++){
        const decision=document.getElementById('decision-'+i).value;
        const notes=document.getElementById('notes-'+i).value.trim();
        if(!decision||!notes){alert('请先完成 '+packet.cases[i].case_id+' 的判断和依据。');return;}
        packet.cases[i].independent_review={reviewer_id:reviewer,date:day,independence_confirmed:true,all_four_inputs_consistent:decision==='true',notes};
      }
      const count=packet.cases.filter(c=>c.independent_review.all_four_inputs_consistent).length;
      packet.status='INDEPENDENT_REVIEW_RECORDED';
      document.getElementById('message').textContent='记录结果：'+count+'/10。'+(count>=9?'达到数量门槛；仍需运行基线与记录检查。':'未达到 9/10 门槛，请保留真实结果并修复问题。');
      const url=URL.createObjectURL(new Blob([JSON.stringify(packet,null,2)],{type:'application/json'}));
      const link=document.createElement('a');link.href=url;link.download='n01-independent-review-packet.json';link.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    };
    </script></html>'''
    path.write_text(page.replace('PACKET',payload))
