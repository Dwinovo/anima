# Frontend

## 概述

当前仓库已经包含一个前端工程：`../apps/admin/`。它是基于 Next.js 16、React 19 和 App Router 的管理台，用来承载 Session 控制面和事件流查看。Entity 客户端仍然只有规格文档，还没有同仓实现。

## 核心要点

- `apps/admin/app/` 是页面入口；`layout.tsx` 已挂载全局 Sidebar 壳，当前只保留两个导航模块：`总览`、`会话`。
- `apps/admin/package.json` 提供 `dev`、`build`、`start`、`lint` 脚本。
- 管理面板 UI 基线统一为 `neobrutalism` 组件风格，组件通过 `shadcn` registry 引入。
- 字体基线：采用“本地字体文件 + 全局变量 + 语义类名”方案。`layout.tsx` 通过 `next/font/local` 注入 `--font-noto-sans-sc`、`--font-noto-serif-sc`、`--font-geist-mono`、`--font-archivo-black`；`globals.css` 映射为 `--font-sans`（正文）、`--font-display`（标题/品牌）、`--font-mono`（数字/ID）。
- 英文字体策略：全站英文统一使用 `--font-sans`（当前指向 `NotoSansCJKsc-VF`），`--font-display` 也与 `--font-sans` 对齐，避免标题、Breadcrumb、Logo 的英文字形不一致。
- 侧边栏会根据当前路由高亮 `总览` 或 `会话`。
- 右侧内容区顶部挂载了 neobrutalism `Breadcrumb`，实时展示 `Anima -> 总览/会话`。
- 右侧布局已对齐 `blaze-point` 的容器节奏：`SidebarInset` 使用 `min-h-svh + px/py`，内部采用 `max-w-6xl` 的 `page-layout`，并拆分为 `page-breadcrumb` 与 `content-surface` 两段。
- Logo 牌为静态展示（无边框、无阴影、无悬浮位移动效），并在侧边栏头部居中布局。
- 品牌资源统一存放在 `apps/admin/public/branding/`；品牌位图标使用 `logo.svg`，品牌英文文本使用本地字体 `ArchivoBlack-Regular.ttf`（`next/font/local` 注入 `--font-archivo-black`）直接渲染，避免 SVG 外链字体失效。
- 右侧内容区（`SidebarInset`）采用语义色 `bg-panel-background`，当前浅色主题值为 `#edf5fe`。
- 管理面板是控制面，职责集中在 Session 管理与事件流查看。
- 前端与服务端的协作边界是 HTTP API，以及 [design-docs/api-contract.md](./design-docs/api-contract.md) 中定义的资源口径。
- Entity 客户端仍由 [product-specs/entity-client-spec.md](./product-specs/entity-client-spec.md) 描述，尚未在本仓库落地。

## 约束

- 不要把前端职责误写回服务端，也不要在 `apps/admin` 中直接依赖 `backend/src/` 的 Python 实现。
- 页面字段和流程必须与 [product-specs/admin-console-spec.md](./product-specs/admin-console-spec.md) 对齐；若冲突，以 API 契约和测试为准。
- 管理面板新页面应优先复用 `components/ui/*` 的 neobrutalism 组件，不要混入其他视觉体系。
- 前端忽略规则统一维护在仓库根目录 `../.gitignore`；没有明确理由时，不要重新添加 `apps/admin/.gitignore`。
- 当前 `overview` 和 `sessions` 页面已接入 Icon + 标题的结构化页头，业务数据区仍待接入。

## 相关文件

- [product-specs/admin-console-spec.md](./product-specs/admin-console-spec.md)
- [product-specs/entity-client-spec.md](./product-specs/entity-client-spec.md)
- [design-docs/api-contract.md](./design-docs/api-contract.md)
- [../apps/admin/package.json](../apps/admin/package.json)
- [../apps/admin/components/ui/sidebar.tsx](../apps/admin/components/ui/sidebar.tsx)
- [../apps/admin/components/ui/breadcrumb.tsx](../apps/admin/components/ui/breadcrumb.tsx)
- [../apps/admin/components/admin-sidebar-nav.tsx](../apps/admin/components/admin-sidebar-nav.tsx)
- [../apps/admin/components/admin-breadcrumb.tsx](../apps/admin/components/admin-breadcrumb.tsx)
- [../apps/admin/app/layout.tsx](../apps/admin/app/layout.tsx)
- [../apps/admin/app/page.tsx](../apps/admin/app/page.tsx)
- [../apps/admin/app/overview/page.tsx](../apps/admin/app/overview/page.tsx)
- [../apps/admin/app/sessions/page.tsx](../apps/admin/app/sessions/page.tsx)
- [../apps/admin/public/branding/logo.svg](../apps/admin/public/branding/logo.svg)
