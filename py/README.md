# 学生学习智能体 (Student Learning Agent)

基于 LangChain/LangGraph 构建的全功能学生学习 AI 智能体，专注于数学、物理、化学三个学科。

## 功能特性

- **智能问答**: 基于 RAG 的知识库问答系统
- **网络搜索**: 集成 SerpAPI 进行实时网络搜索
- **练习生成**: 自动生成各难度级别的练习题
- **作业批改**: 智能批改学生作业并提供详细反馈
- **学习追踪**: 记录和分析学习进度

## 技术栈

- **后端**: FastAPI + LangChain + LangGraph
- **LLM**: DeepSeek V3.2 (ModelScope API)
- **向量数据库**: FAISS
- **搜索**: SerpAPI
- **数据库**: SQLite + SQLAlchemy

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

`.env` 文件已经配置好，包含：
- LLM API 配置 (DeepSeek V3.2)
- SerpAPI 配置

### 3. 导入学习资料 (可选)

将学习资料放入对应目录：
- `data/documents/math/` - 数学资料
- `data/documents/physics/` - 物理资料
- `data/documents/chemistry/` - 化学资料

支持的格式：PDF, TXT, Markdown

运行导入脚本：
```bash
python scripts/ingest_documents.py
```

### 4. 启动服务

```bash
python app/main.py
```

或使用 uvicorn：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问 API

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## API 使用示例

### 发送消息

```bash
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "什么是二次函数？",
    "user_id": "user123"
  }'
```

### 生成练习题

```bash
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "给我生成3道关于二次函数的练习题",
    "user_id": "user123"
  }'
```

## 项目结构

```
student-learning-agent/
├── app/
│   ├── agent/          # LangGraph 智能体
│   ├── api/            # FastAPI 路由
│   ├── core/           # 核心工具
│   ├── db/             # 数据库模型
│   └── services/       # 业务服务
├── data/
│   ├── documents/      # 学习资料
│   └── vector_db/      # 向量存储
├── scripts/            # 工具脚本
└── requirements.txt    # 依赖列表
```

## 智能体工作流

```
用户输入 → Router节点 (意图分类)
    ↓
    ├─→ 知识问答 → RAG检索 → 生成回答
    ├─→ 练习生成 → 生成练习题
    ├─→ 作业批改 → 评分反馈
    └─→ 概念解释 → 详细解释
```

## 开发计划

- [x] 基础架构搭建
- [x] LLM 服务集成
- [x] RAG 知识库系统
- [x] LangGraph 智能体
- [x] FastAPI 接口
- [ ] 前端界面 (React)
- [ ] Docker 部署
- [ ] 学习进度追踪完善
- [ ] 更多练习题类型

## 注意事项

1. 首次运行需要下载嵌入模型，可能需要一些时间
2. 确保 `.env` 文件中的 API 密钥有效
3. 向量数据库会在 `data/vector_db/` 目录下持久化
4. 建议先导入一些学习资料以获得更好的问答效果

## 许可证

MIT License
