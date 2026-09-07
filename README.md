# 发票识别与智能分析系统

## （1）项目简介

### 背景
在企业财务管理和个人报销场景中，人工录入发票信息不仅效率低下，且极易出错。随着 OCR（光学字符识别）技术和大模型（LLM）的发展，自动化识别发票已成为企业数字化转型的标配。本项目旨在利用 Python 构建一个端到端的发票识别系统，实现从图片上传、信息提取到数据可视化分析的全流程自动化。

### 功能描述
* **智能上传**：支持批量上传多种格式（JPG/PNG）的发票图片。
* **多维度识别**：自动提取发票类型、开票单位、受票单位、总金额、税率及日期。
* **图像预处理**：内置图像灰度化、对比度增强与锐化功能，提升复杂背景下的识别精度。
* **实时校对**：提供可编辑的数据表格，允许财务人员对识别结果进行人工微调。
* **数据可视化**：自动生成报销金额统计、供应商支出分布柱状图及发票类型占比饼图。
* **数据导出**：支持一键导出符合财务标准的 CSV 汇总报表。

---

## （2）系统设计

### 架构图
该系统采用经典的“前端展示-后端逻辑-AI引擎”三层架构：
1.  **表现层 (Streamlit)**：负责 Web 交互、文件上传及结果的可视化呈现。
2.  **业务逻辑层 (Pandas & PIL)**：负责数据结构化处理、Session 状态管理及图像增强。
3.  **核心引擎层 (Tesseract OCR)**：负责底层光学字符识别及正则语义提取。

### 技术选型
* **开发语言**：Python 3.13
* **前端框架**：Streamlit (轻量级 Web 开发框架)
* **OCR 引擎**：Tesseract-OCR (开源、支持多语言识别)
* **图像处理**：Pillow (PIL 派生版)
* **数据处理**：Pandas (用于数据汇总与导出)
* **可视化**：Vega-Lite (集成于 Streamlit 的绘图引擎)

---


## （3）核心代码说明

### 1. 图像增强逻辑
```python
def preprocess_image(image):
    gray_image = ImageOps.grayscale(image) # 灰度处理
    enhancer = ImageEnhance.Contrast(gray_image)
    gray_image = enhancer.enhance(1.8)     # 增强对比度提升文字清晰度
    return gray_image

```

### 2. 信息提取（正则匹配）

```python
# 提取金额：寻找包含“金额/合计/￥”等关键词后的数字
amount_match = re.findall(r"(?:金额|合计|￥|¥)\s*[:：]?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2}))", text)
# 提取单位：识别包含“有限公司/中心/集团”的字符串
unit_keywords = r"([^\s\n]*(?:有限公司|股份公司|中心|集团))"

```

### 3. 数据校验与联动

使用 `st.data_editor` 实现 UI 上的实时编辑，修改后的数据会自动同步到后续的统计图表中，体现了“人机共治”的财务理念。

---

## （4）运行说明

### 环境配置

1. **安装 Python 依赖**：
```bash
pip install streamlit pandas Pillow pytesseract

```


2. **安装 OCR 软件**：
* 下载并安装 `Tesseract-OCR`。
* **关键点**：安装时必须勾选 `Chinese (Simplified)` 语言包。
* 在代码中配置 `tesseract_cmd` 路径。



### 启动方式

在项目根目录下打开终端，执行：

```bash
streamlit run app.py

```

---

## （6）效果展示

### 1. 系统主界面

![alt text](data/image1.png)

### 2. 识别与校对明细

![alt text](data/image2.png)

### 3. 财务可视化看板

![alt text](data/image3.png)

### 4. 报表导出

![alt text](data/image4.png)
