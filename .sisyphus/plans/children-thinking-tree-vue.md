# 儿童思维树系统开发计划 (Vue生态版)

## TL;DR
> **Summary**: 基于Vue生态重新设计儿童思维树系统，采用Nuxt 4 + D3.js + GSAP + FastAPI技术栈，分6个阶段实施（包含Wave 0验证阶段），从MVP到完整产品。
> **Deliverables**: 完整的儿童思维树系统，包含前端UI、后端API、AI模型集成、数据库设计、隐私合规架构
> **Effort**: Large (预计8-12个月)
> **Parallel**: YES - 6个主要并行阶段
> **Critical Path**: Wave 0 → 阶段1 → 阶段2 → 阶段3 → 阶段4 → 阶段5

## Context
### Original Request
用户希望根据现有的儿童思维树系统开发计划，理清思路并制定详细的工作计划。用户偏好Vue生态，需要长期开发完整产品。

### Interview Summary
- **帮助方式**: 分析计划优缺点、制定详细工作计划、技术选型建议、分阶段实施策略
- **项目约束**: 完整产品，长期开发
- **技术偏好**: Vue生态（而非React/Next.js）

### Research Findings
1. **Vue树形可视化**: 
   - ❌ `@ssthouse/vue3-tree-chart` 不适用（是组织架构图渲染器，不支持自然树形可视化）
   - ✅ 推荐自定义 D3.js (布局) + GSAP (动画) + Vue 3 (响应式)
   - 备选方案: `vue3-d3-tree`、`TreeWeave`（新兴，零依赖）

2. **Vue全栈方案**: 
   - **首选**: Nuxt 4一体化方案（Hybrid Rendering + Drizzle ORM）
   - **备选**: Nuxt 4（渲染层）+ FastAPI（AI/业务层）混合架构
   - **可选**: Vue 3 + Vite + NestJS（TypeScript全栈统一）

3. **音频AI集成**:
   - 音频录制: AudioWorklet → Float32Array → Int16 PCM 16kHz → Base64
   - Qwen集成: WebSocket流式传输，需要后端代理（浏览器WebSocket不支持自定义headers）
   - MiMo集成: REST API + SSE流式响应，OpenAI兼容格式
   - 隐私保护: 数据最小化、即时清理、HTTPS强制、后端代理保护API密钥

### Metis Review (已完成)
**关键发现**:
1. **树形可视化库选择错误**: `@ssthouse/vue3-tree-chart` 是组织架构图渲染器，不支持自然树形可视化
2. **Nuxt版本混淆**: 必须统一使用Nuxt 4（当前v4.4.4），Nuxt 3 EOL: 2026年7月31日
3. **隐私合规不足**: 仅"处理后删除"不足以满足COPPA/GDPR-K/PIPL要求
4. **浏览器音频兼容性风险**: 不同浏览器的音频格式支持不同，需要兼容性测试

**必须添加的内容**:
- Wave 0 (法律和技术验证) - 在功能代码之前验证隐私合规、浏览器兼容性、AI API访问
- 完整隐私合规架构 - 书面安全计划、同意流程、数据保留/删除政策
- 浏览器兼容性矩阵 - Chrome/Safari/Firefox的音频处理兼容性测试
- 认证系统设计 - JWT/session、教师角色、学校级隔离
- 性能测试目标 - 10/50/100/200节点的渲染时间 < 500ms

## Work Objectives
### Core Objective
将现有的React/Next.js技术方案调整为Vue生态，制定可执行的开发计划，确保项目按时交付。

### Deliverables
1. **技术架构文档**: Vue生态技术栈详细设计
2. **开发计划**: 分阶段任务分解，包含时间线和依赖关系
3. **API设计**: 基于Vue生态的API接口设计
4. **数据库设计**: 适配Vue生态的数据库表结构
5. **部署方案**: Vue应用的部署和运维方案
6. **隐私合规架构**: 完整的儿童数据保护方案

### Definition of Done (verifiable conditions with commands)
- [ ] 所有技术选型有明确的理由和备选方案
- [ ] 所有阶段有具体的验收标准
- [ ] 所有任务有明确的负责人和时间估算
- [ ] 所有依赖关系清晰，无循环依赖
- [ ] 所有风险有应对策略
- [ ] 隐私合规架构通过法律审查
- [ ] 浏览器兼容性矩阵完成
- [ ] 性能测试目标达成

### Must Have
- **Nuxt 4**: 前端框架（统一版本，不再混淆Nuxt 3/4）
- **D3.js + GSAP**: 树形可视化和动画（替代错误的vue3-tree-chart）
- **Pinia**: 状态管理
- **FastAPI**: 后端API和AI模型集成
- **AudioWorklet**: 音频录制和PCM转换
- **隐私合规架构**: 完整的儿童数据保护方案
- **认证系统**: 教师/学校认证和授权

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- **不使用React/Next.js**: 用户明确偏好Vue生态
- **不过度设计**: MVP阶段保持简单，后续迭代
- **不依赖单一AI模型**: 必须支持多模型切换
- **不忽视隐私**: 儿童数据保护必须作为核心设计
- **不跳过Wave 0**: 法律和技术验证必须在功能代码之前完成
- **不使用错误的库**: 不使用@ssthouse/vue3-tree-chart

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: TDD (测试驱动开发) + Vitest
- QA policy: Every task has agent-executed scenarios
- Evidence: .sisyphus/evidence/task-{N}-{slug}.{ext}
- 隐私合规测试: 验证音频删除、数据保留政策、同意流程
- 浏览器兼容性测试: Chrome/Safari/Firefox的音频处理测试
- 性能测试: 10/50/100/200节点的渲染时间测试

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks for max parallelism.

**Wave 0: 法律和技术验证 (5 tasks)**
- 任务0.1: 隐私合规架构设计 + 书面安全计划
- 任务0.2: 认证系统设计 + 教师角色模型
- 任务0.3: 浏览器音频兼容性审计 + PCM转换原型
- 任务0.4: AI API访问验证 + WebSocket代理测试
- 任务0.5: 树形可视化原型 (D3+GSAP)

**Wave 1: 基础架构搭建 (3 tasks)**
- 任务1.1: Nuxt 4项目初始化 + 基础配置
- 任务1.2: FastAPI后端初始化 + 数据库设计
- 任务1.3: 开发环境搭建 + CI/CD配置

**Wave 2: MVP功能开发 (4 tasks)**
- 任务2.1: 活动管理API + 前端页面
- 任务2.2: 树节点管理API + 前端组件
- 任务2.3: 基础树形UI实现 (D3+GSAP)
- 任务2.4: 数据持久化 + 状态管理

**Wave 3: AI集成 (3 tasks)**
- 任务3.1: 音频录制组件 + AudioWorklet集成
- 任务3.2: AI模型适配层设计 + Qwen集成
- 任务3.3: 教师确认流程 + 候选节点管理

**Wave 4: 视觉升级 (3 tasks)**
- 任务4.1: SVG树形渲染优化
- 任务4.2: 动画效果实现 (GSAP)
- 任务4.3: 响应式设计 + 触摸支持

**Wave 5: AI助手 + 完善 (4 tasks)**
- 任务5.1: AI追问建议功能
- 任务5.2: 智能建议功能
- 任务5.3: 回顾功能 + 数据统计
- 任务5.4: 导出功能 + 性能优化

### Dependency Matrix (full, all tasks)
- 任务0.1 → 所有任务 (隐私合规基础)
- 任务0.2 → 任务1.1, 任务1.2 (认证系统)
- 任务0.3 → 任务3.1 (音频兼容性)
- 任务0.4 → 任务3.2 (AI API)
- 任务0.5 → 任务2.3, 任务4.1, 任务4.2 (树形可视化)
- 任务1.1 → 任务2.1, 任务2.2, 任务2.3, 任务2.4
- 任务1.2 → 任务2.1, 任务2.2, 任务3.2
- 任务1.3 → 所有任务
- 任务2.1 → 任务3.1, 任务3.3
- 任务2.2 → 任务3.1, 任务3.3
- 任务2.3 → 任务4.1, 任务4.2
- 任务2.4 → 任务3.3, 任务5.3
- 任务3.1 → 任务3.2
- 任务3.2 → 任务3.3, 任务5.1, 任务5.2
- 任务3.3 → 任务5.1, 任务5.2
- 任务4.1 → 任务4.2, 任务4.3
- 任务4.2 → 任务4.3
- 任务5.1 → 任务5.3
- 任务5.2 → 任务5.3
- 任务5.3 → 任务5.4

### Agent Dispatch Summary (wave → task count → categories)
- Wave 0: 5 tasks → unspecified-high, deep, writing
- Wave 1: 3 tasks → quick, unspecified-low
- Wave 2: 4 tasks → unspecified-high, visual-engineering
- Wave 3: 3 tasks → unspecified-high, deep
- Wave 4: 3 tasks → visual-engineering, artistry
- Wave 5: 4 tasks → unspecified-high, deep, writing

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: Agent Profile + Parallelization + QA Scenarios.

- [ ] 0.1 隐私合规架构设计 + 书面安全计划

  **What to do**: 
  - 设计完整的隐私合规架构，满足COPPA/GDPR-K/PIPL要求
  - 创建书面安全计划：指定安全官、音频收集风险评估、保障措施、定期测试、年度评估
  - 设计两级同意架构：学校代理同意（仅限教育用途）+ 家长单独同意机制
  - 制定数据保留/删除政策文档
  - 创建数据处理协议模板（用于Qwen/MiMo API供应商）
  - 设计数据泄露通知流程（72小时GDPR通知模板）
  - 创建年度合规审计计划（中国CAC年度报告）

  **Must NOT do**: 
  - 不要跳过任何法律要求
  - 不要假设"处理后删除"就足够了

  **Recommended Agent Profile**:
  - Category: `writing` - Reason: 法律文档和合规架构设计
  - Skills: [`legal`, `privacy`] - [why needed]
  - Omitted: [`playwright`] - [why not needed]

  **Parallelization**: Can Parallel: YES | Wave 0 | Blocks: [所有任务] | Blocked By: []

  **References** (executor has NO interview context - be exhaustive):
  - Pattern: `https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa` - [COPPA规则]
  - API/Type: `https://gdpr-info.eu/art-8-gdpr/` - [GDPR第8条]
  - Test: `https://www.cac.gov.cn/` - [中国网信办]
  - External: `https://www.ftc.gov/news-events/news/press-releases/2023/05/ftc-orders-amazon-pay-25-million-over-alexa-privacy-violations` - [Amazon Alexa罚款案例]

  **Acceptance Criteria** (agent-executable only):
  - [ ] 书面安全计划文档完成
  - [ ] 两级同意架构设计完成
  - [ ] 数据保留/删除政策文档完成
  - [ ] 数据处理协议模板完成
  - [ ] 数据泄露通知流程设计完成
  - [ ] 年度合规审计计划完成

  **QA Scenarios** (MANDATORY - task incomplete without these):
  ```
  Scenario: 隐私合规文档完整性
    Tool: read
    Steps: 检查所有隐私合规文档是否包含必要元素
    Expected: 所有文档包含COPPA/GDPR-K/PIPL要求的元素
    Evidence: .sisyphus/evidence/task-0-1-privacy-docs.md

  Scenario: 同意流程设计
    Tool: read
    Steps: 检查两级同意架构设计
    Expected: 学校代理同意和家长单独同意机制设计完整
    Evidence: .sisyphus/evidence/task-0-1-consent-flow.md
  ```

  **Commit**: YES | Message: `docs: design privacy compliance architecture` | Files: [docs/privacy/, docs/compliance/]

- [ ] 0.2 认证系统设计 + 教师角色模型

  **What to do**: 
  - 设计认证架构（JWT/session）
  - 创建教师角色模型（管理员、普通教师、观察者）
  - 设计学校级隔离策略
  - 设计API认证中间件
  - 创建认证流程图和威胁模型文档
  - 设计密码策略和会话管理

  **Must NOT do**: 
  - 不要实现完整认证系统，只设计架构
  - 不要添加不必要的安全特性

  **Recommended Agent Profile**:
  - Category: `unspecified-high` - Reason: 认证架构设计，需要安全知识
  - Skills: [`security`, `authentication`] - [why needed]
  - Omitted: [`playwright`] - [why not needed]

  **Parallelization**: Can Parallel: YES | Wave 0 | Blocks: [1.1, 1.2] | Blocked By: []

  **References** (executor has NO interview context - be exhaustive):
  - Pattern: `https://auth0.com/docs` - [Auth0文档]
  - API/Type: `https://jwt.io/` - [JWT标准]
  - Test: `https://owasp.org/www-project-web-security-testing-guide/` - [OWASP测试指南]
  - External: `https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html` - [OWASP认证备忘录]

  **Acceptance Criteria** (agent-executable only):
  - [ ] 认证架构决策文档完成
  - [ ] 教师角色模型设计完成
  - [ ] 学校级隔离策略设计完成
  - [ ] API认证中间件设计完成
  - [ ] 认证流程图和威胁模型文档完成

  **QA Scenarios** (MANDATORY - task incomplete without these):
  ```
  Scenario: 认证架构设计
    Tool: read
    Steps: 检查认证架构设计文档
    Expected: 包含JWT/session决策、角色模型、隔离策略
    Evidence: .sisyphus/evidence/task-0-2-auth-design.md

  Scenario: 威胁模型文档
    Tool: read
    Steps: 检查威胁模型文档
    Expected: 包含认证流程图和威胁分析
    Evidence: .sisyphus/evidence/task-0-2-threat-model.md
  ```

  **Commit**: YES | Message: `docs: design authentication system architecture` | Files: [docs/auth/, docs/security/]

- [ ] 0.3 浏览器音频兼容性审计 + PCM转换原型

  **What to do**: 
  - 创建浏览器兼容性矩阵（Chrome/Safari/Firefox/iOS Safari）
  - 实现AudioWorklet PCM转换原型
  - 测试不同浏览器的音频格式支持
  - 设计Firefox回退方案（客户端重采样）
  - 创建音频处理管道文档
  - 测试麦克风权限处理

  **Must NOT do**: 
  - 不要假设所有浏览器支持相同
  - 不要忽略iOS Safari的限制

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: 浏览器兼容性测试，需要深入技术知识
  - Skills: [`audio`, `browser-compatibility`] - [why needed]
  - Omitted: [`playwright`] - [why not needed]

  **Parallelization**: Can Parallel: YES | Wave 0 | Blocks: [3.1] | Blocked By: []

  **References** (executor has NO interview context - be exhaustive):
  - Pattern: `https://developer.mozilla.org/en-US/docs/Web/API/AudioWorklet` - [MDN AudioWorklet]
  - API/Type: `https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder` - [MDN MediaRecorder]
  - Test: `https://developer.mozilla.org/en-US/docs/Web/API/AudioContext` - [MDN AudioContext]
  - External: `https://caniuse.com/` - [浏览器兼容性查询]

  **Acceptance Criteria** (agent-executable only):
  - [ ] 浏览器兼容性矩阵文档完成
  - [ ] AudioWorklet PCM转换原型工作
  - [ ] Firefox回退方案设计完成
  - [ ] 音频处理管道文档完成
  - [ ] 麦克风权限处理测试完成

  **QA Scenarios** (MANDATORY - task incomplete without these):
  ```
  Scenario: PCM转换测试
    Tool: interactive_bash
    Steps: 运行PCM转换原型，验证输出格式
    Expected: 输出16kHz/16bit/mono PCM格式
    Evidence: .sisyphus/evidence/task-0-3-pcm-test.png

  Scenario: 浏览器兼容性测试
    Tool: playwright
    Steps: 在Chrome/Safari/Firefox中测试音频录制
    Expected: 所有浏览器支持音频录制
    Evidence: .sisyphus/evidence/task-0-3-browser-test.png
  ```

  **Commit**: YES | Message: `feat: implement AudioWorklet PCM conversion prototype` | Files: [src/audio/, docs/browser-compatibility/]

- [ ] 0.4 AI API访问验证 + WebSocket代理测试

  **What to do**: 
  - 验证Qwen DashScope API密钥和连接
  - 实现FastAPI WebSocket代理原型
  - 测试WebSocket音频流传输
  - 验证MiMo API访问
  - 创建API成本估算文档
  - 设计API错误处理策略

  **Must NOT do**: 
  - 不要在前端直接暴露API密钥
  - 不要忽略API限流和错误处理

  **Recommended Agent Profile**:
  - Category: `deep` - Reason: AI API集成，需要深入技术知识
  - Skills: [`api-integration`, `websocket`] - [why needed]
  - Omitted: [`playwright`] - [why not needed]

  **Parallelization**: Can Parallel: YES | Wave 0 | Blocks: [3.2] | Blocked By: []

  **References** (executor has NO interview context - be exhaustive):
  - Pattern: `https://help.aliyun.com/zh/model-studio/realtime` - [Qwen Realtime文档]
  - API/Type: `https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/multimodal-understanding/audio-understanding` - [MiMo音频理解文档]
  - Test: `https://fastapi.tiangolo.com/advanced/websockets/` - [FastAPI WebSocket]
  - External: `https://dashscope.aliyuncs.com/` - [DashScope控制台]

  **Acceptance Criteria** (agent-executable only):
  - [ ] Qwen API密钥验证成功
  - [ ] FastAPI WebSocket代理原型工作
  - [ ] WebSocket音频流传输测试通过
  - [ ] MiMo API访问验证成功
  - [ ] API成本估算文档完成
  - [ ] API错误处理策略设计完成

  **QA Scenarios** (MANDATORY - task incomplete without these):
  ```
  Scenario: WebSocket代理测试
    Tool: interactive_bash
    Steps: 启动FastAPI代理，发送测试音频
    Expected: 代理成功转发音频到Qwen API
    Evidence: .sisyphus/evidence/task-0-4-websocket-test.png

  Scenario: API错误处理测试
    Tool: interactive_bash
    Steps: 模拟API错误，检查错误处理
    Expected: 错误被正确捕获和处理
    Evidence: .sisyphus/evidence/task-0-4-error-handling.png
  ```

  **Commit**: YES | Message: `feat: implement FastAPI WebSocket proxy prototype` | Files: [src/api/, docs/api/]

- [ ] 0.5 树形可视化原型 (D3+GSAP)

  **What to do**: 
  - 创建D3.js树形布局原型
  - 实现GSAP动画效果（微风摇动、新叶生长）
  - 设计自然曲线枝干渲染
  - 创建叶片形状节点
  - 测试性能（10/50/100/200节点）
  - 创建树形可视化文档

  **Must NOT do**: 
  - 不要使用@ssthouse/vue3-tree-chart（不适用）
  - 不要忽略性能测试

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: 树形可视化，需要视觉设计知识
  - Skills: [`d3js`, `gsap`, `svg`] - [why needed]
  - Omitted: [`playwright`] - [why not needed]

  **Parallelization**: Can Parallel: YES | Wave 0 | Blocks: [2.3, 4.1, 4.2] | Blocked By: []

  **References** (executor has NO interview context - be exhaustive):
  - Pattern: `https://d3js.org/` - [D3.js文档]
  - API/Type: `https://gsap.com/docs/` - [GSAP文档]
  - Test: `https://developer.mozilla.org/en-US/docs/Web/SVG` - [MDN SVG]
  - External: `https://observablehq.com/@d3/gallery` - [D3示例]

  **Acceptance Criteria** (agent-executable only):
  - [ ] D3.js树形布局原型工作
  - [ ] GSAP动画效果实现
  - [ ] 自然曲线枝干渲染完成
  - [ ] 叶片形状节点创建完成
  - [ ] 性能测试通过（100节点 < 500ms）
  - [ ] 树形可视化文档完成

  **QA Scenarios** (MANDATORY - task incomplete without these):
  ```
  Scenario: 树形渲染测试
    Tool: playwright
    Steps: 渲染树形可视化，检查视觉效果
    Expected: 树形可视化看起来自然，有曲线枝干和叶片
    Evidence: .sisyphus/evidence/task-0-5-tree-render.png

  Scenario: 性能测试
    Tool: interactive_bash
    Steps: 测试不同节点数量的渲染时间
    Expected: 100节点渲染时间 < 500ms
    Evidence: .sisyphus/evidence/task-0-5-performance.png
  ```

  **Commit**: YES | Message: `feat: implement D3+GSAP tree visualization prototype` | Files: [src/components/Tree/, docs/visualization/]

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay.** Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.
- [ ] F1. Plan Compliance Audit — oracle
- [ ] F2. Code Quality Review — unspecified-high
- [ ] F3. Real Manual QA — unspecified-high (+ playwright if UI)
- [ ] F4. Scope Fidelity Check — deep

## Commit Strategy
- 每个任务完成后提交一次
- 提交信息格式: `type(scope): description`
- 类型: feat, fix, chore, docs, test, refactor
- 范围: frontend, backend, database, api, ui, etc.

## Success Criteria
1. **技术栈明确**: Vue生态技术选型有明确理由和备选方案
2. **阶段清晰**: 6个阶段有具体的验收标准和时间估算
3. **任务可执行**: 所有任务有明确的负责人和依赖关系
4. **风险可控**: 所有风险有应对策略
5. **质量保证**: 有完整的测试和CI/CD流程
6. **隐私合规**: 完整的儿童数据保护方案
7. **浏览器兼容**: 完整的浏览器兼容性矩阵
8. **性能达标**: 100节点渲染时间 < 500ms
