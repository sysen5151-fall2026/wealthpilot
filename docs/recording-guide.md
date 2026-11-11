# WealthPilot 露脸录屏指南

目标：约 10 分钟，露脸开场和结尾，中间共享屏幕并保留摄像头小窗。以下时间包含操作、指图和翻页；不要为凑时间逐字朗读所有编号。

## 录制前必须完成

1. 确认课堂演示选择的是 F.6；本次必须用同一函数。
2. 根据 docs/model-recording-checklist.md 核对当前 Innoslate。云端关系未确认前，不读讲稿中声称已经展示该关系的句子。
3. 请有写入权限的队友把本次更新合并到最新仓库，保留隐藏的 .github 文件夹，等待真实 GitHub Actions 成功。当前连接对课程仓库只有读取权限，本地通过不等于云端 CI 已通过。
4. 团队确认规则审批状态；未经团队确认，不把 team sign-off pending 改成 approved。
5. 提前启动 demo、登录 Innoslate，打开模型图和代码文件。录制时不安装依赖、不登录、不等待 CI。

## Mac 上如何露脸加屏幕录制

使用 Zoom 桌面版，自己主持一个会议，开启摄像头和麦克风。先共享屏幕，再使用 Record → Record on this Computer（如账户允许）。录 20 秒测试片，停止并结束会议，等转换完成后打开 MP4，确认人脸、屏幕文字和声音都被录入。正式录制时重新开会，先不共享以露脸开场，再共享屏幕讲解，最后停止共享以露脸总结。录制结束后等转换完成，不要立即关电脑。

Zoom 官方操作参考：https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0076922 。账户管理员可能限制本地录制；如果按钮不可用，先解决权限再正式录。

摄像头画面尽量放在空白区域，不遮模型下方机制、代码参数和测试摘要。建议屏幕 16:9、文字放大、开启勿扰，关闭聊天通知。共享整个桌面便于切应用；共享之前先关闭私人窗口。

## 启动与测试

在项目文件夹双击 Launch_WealthPilot.command。也可以在终端进入该文件夹后运行：

```bash
zsh Launch_WealthPilot.command
```

浏览器打开 http://127.0.0.1:8000/ 。这是本机演示地址，录屏不要求同学从自己电脑访问。保持运行服务器的终端打开。首次安装可能需要几分钟，提前完成。

另开一个终端，在项目文件夹执行：

```bash
.venv/bin/python -m pytest tests/test_functional_requirements.py tests/test_model_contract.py -v
.venv/bin/python -m pytest -q -rs
```

当前实测结果：131 passed, 0 skipped。八项课程验收按 SPEC.md 的 AI 角色方法执行；不是招募真人的用户研究。GitHub Actions 仍须推送后运行。

## 固定演示数据

- Goal：Retirement；Years：25；Cash：25000；Monthly contribution：500；Annual income：85000；Age：34；Early need：Unlikely。
- Holding：VTI，5000。
- 问卷：Hold and wait；A little；20%；Balanced growth；Somewhat stable。
- 当前快照和规则下预期风险分数 70，类别 Moderately Aggressive，计划总额 30000。只有在配置没有改动时才预期这些数值。
- 为节省视频时间，可先把表单填好停在问卷页；在镜头里简要说明输入，重点展示确认、生成、保存和回读。不要在录制时删除数据库。

## 提前打开的页面

1. Innoslate：物理一级 IDEF0、F.6 二级 IDEF0、功能层级、资产层级、需求追踪。
2. WealthPilot：本机 demo。
3. 编辑器：docs/traceability.md、save_authorization.py、contracts/api-v1.yaml、docs/route-table.md、tests/test_functional_requirements.py。
4. GitHub：与本次代码提交对应的成功 Actions 运行，不用旧提交的绿色记录。
5. 第二屏/纸张：英文讲稿。不要把整段讲稿共享给观众。

## 十分钟中文操作提示与英文讲稿

### 0:00–0:35 露脸开场

屏幕操作：摄像头大画面。介绍自己；随后开始共享浏览器。

English script:

Hello, I’m Fangziyue Zhang. This is our Milestone Two demonstration of WealthPilot, an educational investment-planning simulator. Today I will connect one modeled function to the running product, its code, and its requirement tests. Our selected function is F.6, Manage Investment Plan Delivery. WealthPilot uses hypothetical inputs and historical data. It does not place real trades or move real money.

### 0:35–1:15 物理 IDEF0

屏幕操作：共享 Innoslate 一级物理 IDEF0。指向 F.6 和底部 C.6；确认画面真实有该关系。

English script:

This is the physical IDEF0 view. The functions describe what the system does. The mechanisms underneath identify the assets that perform those functions. F.6 is performed by C.6, the Investment Plan Management Subsystem. It receives investment recommendations and weights from F.5. Explanation Rules govern its wording, and a Plan Save Request controls whether the reviewed plan can be saved. Its outputs distinguish the explanation, the presented plan, the saved plan, and the save confirmation.

### 1:15–2:15 二级 IDEF0 和两张层级图

屏幕操作：依次展示 F.6 二级图、功能层级、资产层级。每张停留约 10 秒；沿五个函数和内部流指一遍。

English script:

F.6 decomposes into five functions. F.6.1 explains the plan, and F.6.2 presents it and creates a reviewed snapshot. F.6.3 validates explicit save authorization. F.6.4 persists the authorized snapshot. F.6.5 releases the saved plan and confirmation only after successful persistence. The internal flows are the reviewed snapshot, the authorized save payload, and the persistence result. The explanation also passes from F.6.1 to F.6.2. Here, the function hierarchy shows the five responsibilities. The asset hierarchy shows the five corresponding components under C.6. These are the same function and component identifiers used in the application trace and module documentation.

### 2:15–3:05 输入与风险确认

屏幕操作：切到 localhost 首页。快速填准备好的虚拟数据，不要逐项朗读。点 See my risk profile，指出 70 分，再点 Yes, build my plan。

English script:

I will use a fictional investor so that no personal financial information is needed. The investor is planning for retirement in twenty-five years, with twenty-five thousand dollars of cash and five thousand dollars in an existing VTI holding. The questionnaire produces a risk score of seventy for this example. The investor sees the interpretation before choosing to build a plan. This confirmation is separate from authorization to save. The earlier functions prepare the recommendations that become F.6’s input.

### 3:05–4:20 解释 保存 与回读

屏幕操作：展示 Why this plan、Risks to know。保存前停 2 秒；点 Save this simulated plan；展示现金/持仓前后表；点 See saved plans 并打开计划。

English script:

The plan now shows the allocation, individual securities, and simulated amounts. The explanation connects the result to the investor’s profile and identifies material risks. Historical figures describe the recorded sample; they are not forecasts. At this point, the investor has reviewed the plan but has not authorized saving. Now I select Save this simulated plan. The application validates that the request refers to the reviewed plan, persists the content, and confirms success. The before-and-after table shows that cash remains twenty-five thousand dollars and the VTI holding remains five thousand dollars. Saving preserves a planning document; it does not execute a portfolio change. I can reopen the saved plan and review the same content.

### 4:20–5:00 产品追踪与追踪表

屏幕操作：回到当前计划，展开 How this plan was built。随后打开 docs/traceability.md 的 F.6.1–F.6.5 行。

English script:

This trace records the functions and assets as they actually run. The save path follows F.6.3, F.6.4, and F.6.5. In docs/traceability.md, each row links a function to its performing asset, module, requirement identifiers, and named tests. For example, F.6.3 maps to the save authorization module, requirement CS6.1.4.3, and tests for valid and invalid requests. This provides a concrete path from a box in the model to executable behavior.

### 5:00–6:00 模块与 ICOM

屏幕操作：打开 investment_plan_management/save_authorization.py。先指文件顶部说明，再指函数参数，最后指失效请求返回 None 的逻辑。

English script:

The module documentation identifies F.6.3 and its performing component, C.6.3. Its signature follows the ICOMs: the reviewed snapshot is the input, and the Plan Save Request is a control. The output is an authorized save payload. A missing request, a view event, an empty request identifier, or a different plan identifier cannot authorize saving. The persistence module then takes the authorized payload and a repository adapter. It reports success only after reading back the complete stored content. The confirmation module checks the persistence result before issuing a successful-save message.

### 6:00–6:45 接口契约与路由表

屏幕操作：打开 contracts/api-v1.yaml，搜索 x-model-operations 和 x-model-flows；再打开 docs/route-table.md 的保存一行。

English script:

The API contract separates real HTTP routes from internal Python operations. Under x-model-operations, the five F.6 calls list their inputs, controls, outputs, mechanisms, and requirement identifiers. The internal-flow section links each producer to its consumer and payload schema. These internal calls are not invented network endpoints. The route table maps the product action to UC.1: selecting Save this simulated plan invokes the plan-save-requests route, which serves the authorization, persistence, and confirmation steps.

### 6:45–8:05 需求与向下分配

屏幕操作：切回 Innoslate。展示父需求 1.4.7、组件 CS6.1.4.4，以及组件输入/输出/接口需求。再展示已核对的系统安全需求与 CS6.2.4 关系。只有真实核对并记录方法后才读此段。

English script:

Here I trace the parent save obligation to the component specification. The parent requires saving only after an explicit request. The component-level requirements separate authorization, persistence, and confirmation, with input, output, and interface obligations. Requirement 1.4.8 separately protects simulated portfolio state during saving. For the system-wide example, the educational-simulation safety constraint is allocated to the plan-delivery component using equivalence within that component’s scope. The prohibition on real execution is retained rather than divided into a numerical budget. The component may explain, present, and save an educational plan, but it may not convert that process into real trading. The recorded link and rationale make that allocation reviewable.

### 8:05–9:30 指定测试与真实 CI

屏幕操作：打开 tests/test_functional_requirements.py，搜索 test_CS6_1_4_3_invalid_requests_produce_no_payload 和 test_CS6_1_4_4_failed_write_is_not_reported_as_success。展示本地测试摘要，然后展示已运行成功的 GitHub Actions 页面。

English script:

These tests are named by requirement identifier. They check the successful path and meaningful failure paths, including invalid authorization, a mismatched plan, write failure, incomplete persistence, and suppression of false confirmation. The state-preservation test compares the simulated portfolio before and after saving. Contract tests also compare the published specification with actual signatures and serialized payloads. All one hundred thirty-one local checks pass, with no skips. The eight coursework acceptance checks use AI-authored role protocols against actual application responses, as permitted for the course according to our TA guidance. The report states that method; it is not a human usability study. Two operator processes reproduce the baseline, and two recovery exercises restore it. Hosted CI must still run after this update is pushed; local output alone is not a GitHub Actions result.

### 9:30–10:00 露脸总结

屏幕操作：停止共享屏幕，摄像头大画面收尾。

English script:

The demonstrated chain is consistent: F.6 decomposes into five modeled responsibilities, the product follows those responsibilities, and the code and tests use the same identifiers and data flows. The key boundary is explicit authorization: the reviewed plan is saved only when requested, confirmation follows successful persistence, and simulated cash and holdings remain unchanged. Thank you.

## 不能混淆的说法

- 当前默认解释来自模板。只有实际启用了并验证 LM Studio 时才说正在用语言模型。
- GitHub CI 没运行成功前，把 CI 段留给队友处理；不要读“This GitHub Actions run...”冒充已完成。
- 若只是练习，可以替换为：“The local tests pass. A hosted CI run is still pending, so this is not yet our final submission recording.” 这句话是诚实说明，不代表已经满足作业的 CI 要求。
- 不能把“性能/可用性未验证”说成通过，不能把代码中写了模型 ID 说成云端模型关系已核对。

## 把代码交给有写入权限的队友

先获取远端最新版本，按 CHANGES.md 合并本次改动，避免用旧压缩包覆盖队友的新代码。提交 contracts、docs、scripts、测试重命名、requirements-dev.txt、README、启动脚本和 .github/workflows/tests.yml。推送后在 Actions 找到对应提交，确认每个步骤成功并下载测试报告。录制时展示这次运行的提交号和结果。

## 提交前回放检查

脸和声音清晰；页面字够大；每张要求的模型图都出现；展示模块说明和 ICOM 参数；展示契约、路由表、指定测试和真实 CI；展示系统级需求分配的方法；整段约十分钟。导出 MP4 并从头到尾回放后，再按课程 Canvas 的视频提交方式上传。这里只准备材料，不代你录制或提交。
