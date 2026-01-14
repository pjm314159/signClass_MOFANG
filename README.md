# 课堂签到系统 - 重构版

## 项目概述

本项目是一个课堂签到自动化系统，支持多种签到方式（位置签到、密码签到、二维码签到、点名签到），通过微信扫码登录，自动监控并完成签到任务。  
支持通过教师版登录，来全自动签到

## 项目结构

```
signClass/
├── config/                    # 配置模块
│   ├── __init__.py
│   └── config_manager.py     # YAML配置文件管理
├── core/                     # 核心模块
│   ├── __init__.py
│   └── scheduler.py          # 任务调度器
├── infrastructure/           # 基础设施层
│   ├── __init__.py
│   └── logger.py            # 日志系统
├── models/                   # 数据模型层
│   ├── __init__.py
│   └── sign_data.py         # 签到数据模型
├── service/                  # 服务层
│   ├── crawler/             # 数据爬取模块
│   │   ├── __init__.py
│   │   └── crawlSign.py     # 签到数据爬取
│   ├── login/               # 登录模块
│   │   ├── __init__.py
│   │   ├── login.py         # 登录逻辑
│   │   └── QRApp.py         # 二维码应用
│   ├── pipeline/            # 数据处理管道
│   │   ├── __init__.py
│   │   ├── extractors.py    # 数据提取器
│   │   └── transformer.py   # 数据转换器
│   └── signer/              # 签到执行模块
│       ├── __init__.py
│       └── signer_core.py   # 签到核心逻辑
├── gui/                     # 图形界面
│   ├── __init__.py
│   ├── main_ui.py           # 主界面
│   └── qr_login_dialog.py   # 二维码登录对话框
├── test/                    # 测试目录
│   ├── test.py              # 测试文件
│   └── showQrcode.py        # 二维码测试
├── assets/                  # 资源目录
├── main.py                  # 主入口文件
├── config.yaml              # 配置文件
├── requirements.txt         # 依赖包列表
├── app.log                  # 日志文件
├── .gitignore              # Git忽略文件
└── favicon.ico             # 应用图标
```

## 核心功能模块

### 1. 配置模块 (config/)
- **config_manager.py**: 使用YAML格式管理配置，支持配置初始化、加载和保存
- 主要配置项：
  - 系统设置（签到间隔、延时等）
  - 位置信息（默认经纬度）
  - 日志配置（级别、文件、轮转等）
  - URL配置（登录地址、域名等）
  - 用户登录数据

### 2. 基础设施层 (infrastructure/)
- **logger.py**: 自定义日志系统，支持控制台和文件输出，配置化日志级别和轮转

### 3. 数据模型 (models/)
- **sign_data.py**: 使用dataclass定义签到和班级数据模型
  - `Sign`: 签到信息（类型、状态、过期时间、班级ID、特定参数等）
  - `Class`: 班级信息（ID、名称、签到列表）

### 4. 登录模块 (service/login/)
- **login.py**: 微信扫码登录逻辑，支持学生版和教师版登录
- **QRApp.py**: 二维码展示和登录状态监听
- 二维码显示功能集成在GUI模块的`qr_login_dialog.py`中

### 5. 数据爬取模块 (service/crawler/)
- **crawlSign.py**: 爬取课程和签到信息，解析HTML页面，提取签到数据

### 6. 数据处理管道 (service/pipeline/)
- **extractors.py**: 数据提取器
- **transformer.py**: 数据转换器，处理signId缺失等情况

### 7. 签到执行模块 (service/signer/)
- **signer_core.py**: 执行各种签到类型：
  - 位置签到
  - 密码签到
  - 二维码签到
  - 点名签到

### 8. 核心调度器 (core/)
- **scheduler.py**: 任务调度和管理，协调各个模块工作流程

## 支持的签到类型

1. **位置签到 (GPS)**
   - 支持默认位置配置
   - 支持特定位置参数传递
   - 可选是否需要图片验证

2. **密码签到**
   - 4位数字密码
   - 暴力破解机制
   - 自动尝试直到成功

3. **二维码签到**
   - 无法直接获取signId
   - 可以通过教师版登录获取signId,，向后猜来获signId


4. **点名签到**
   - 无法直接获取signId

## 技术特点

1. **模块化设计**: 清晰的层级结构（基础设施层、配置层、服务层、交互层）
2. **配置化**: 使用YAML配置文件，支持配置初始化和管理
3. **日志系统**: 完整的日志记录和轮转机制
4. **数据模型**: 使用Python dataclass定义结构化数据
5. **异常处理**: 完善的错误处理和恢复机制
6. **GUI界面**: 基于wxPython的图形用户界面，支持系统托盘图标和实时日志显示

## 依赖库

- `requests`: HTTP请求库
- `beautifulsoup4`: HTML解析库
- `qrcode`: 二维码生成
- `wxPython`: 图形界面开发
- `PyYAML`: YAML配置文件处理
- `lxml`: XML/HTML解析

## 使用方式

### 1. 环境准备
```bash
# 安装依赖包
pip install -r requirements.txt
```

### 2. 启动程序
```bash
# 直接启动图形界面
python main.py
```

首次运行会自动生成 `config.yaml` 配置文件，您可以在其中配置：
- 签到监控间隔时间
- 默认地理位置
- 日志设置
- 登录相关URL
- 用户登录数据（扫码登录后自动保存）
对于无法获取signId的情况，如果需要全自动签到，则not_find_signId改为1，并把要发布签到的班级class_id填上，class_id你可以通过网址获得
否则为0的情况，就是手动输入signId进行签到

### 3. 使用流程
1. 首次启动程序后，点击"登录"按钮
2. 使用微信扫描弹出的二维码
3. 登录成功后，点击"开始"按钮开始监控签到
4. 系统会自动检测并完成各种类型的签到


## 注意事项

- 本项目仅为技术学习和研究使用
- 使用前请确保遵守相关平台的使用规定
- 配置文件包含敏感信息，请注意安全保护
