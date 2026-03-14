# Frontend

## 概述

当前仓库已经包含一个前端工程：`../apps/admin/`。它是基于 Next.js 16、React 19 和 App Router 的管理台，用来承载 Session 控制面和事件流查看。Entity 客户端仍然只有规格文档，还没有同仓实现。

## 核心要点

- `apps/admin/app/` 是页面入口；`layout.tsx` 已挂载全局 Sidebar 壳，当前只保留两个导航模块：`总览`、`会话`。
- `apps/admin/package.json` 提供 `dev`、`build`、`start`、`lint` 脚本。
- 管理面板 UI 基线统一为 `neobrutalism` 组件风格，组件通过 `shadcn` registry 引入。
- 字体基线：正文使用 `NotoSansCJKsc`，标题使用 `NotoSerifCJKsc`，通过 `app/fonts` 的本地字体变量注入。
- 侧边栏会根据当前路由高亮 `总览` 或 `会话`。
- Logo 牌仅保留 hover 动效，不提供按下态点击反馈。
- 右侧内容区（`SidebarInset`）当前统一使用 `#dcebfe` 背景色。
- 管理面板是控制面，职责集中在 Session 管理与事件流查看。
- 前端与服务端的协作边界是 HTTP API，以及 [design-docs/api-contract.md](./design-docs/api-contract.md) 中定义的资源口径。
- Entity 客户端仍由 [product-specs/entity-client-spec.md](./product-specs/entity-client-spec.md) 描述，尚未在本仓库落地。

## 约束

- 不要把前端职责误写回服务端，也不要在 `apps/admin` 中直接依赖 `backend/src/` 的 Python 实现。
- 页面字段和流程必须与 [product-specs/admin-console-spec.md](./product-specs/admin-console-spec.md) 对齐；若冲突，以 API 契约和测试为准。
- 管理面板新页面应优先复用 `components/ui/*` 的 neobrutalism 组件，不要混入其他视觉体系。
- 前端忽略规则统一维护在仓库根目录 `../.gitignore`；没有明确理由时，不要重新添加 `apps/admin/.gitignore`。
- 当前 `overview` 和 `sessions` 页面内容为空白占位；在真实功能接入前不要将其视为完成状态。

## 相关文件

- [product-specs/admin-console-spec.md](./product-specs/admin-console-spec.md)
- [product-specs/entity-client-spec.md](./product-specs/entity-client-spec.md)
- [design-docs/api-contract.md](./design-docs/api-contract.md)
- [../apps/admin/package.json](../apps/admin/package.json)
- [../apps/admin/components/ui/sidebar.tsx](../apps/admin/components/ui/sidebar.tsx)
- [../apps/admin/components/admin-sidebar-nav.tsx](../apps/admin/components/admin-sidebar-nav.tsx)
- [../apps/admin/app/fonts](../apps/admin/app/fonts)
- [../apps/admin/app/layout.tsx](../apps/admin/app/layout.tsx)
- [../apps/admin/app/page.tsx](../apps/admin/app/page.tsx)
- [../apps/admin/app/overview/page.tsx](../apps/admin/app/overview/page.tsx)
- [../apps/admin/app/sessions/page.tsx](../apps/admin/app/sessions/page.tsx)
