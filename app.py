import streamlit as st
import pytesseract
import pandas as pd
from PIL import Image, ImageOps, ImageEnhance
import re
import io
import numpy as np

# 1. 路径配置（请确保此路径与你安装的 Tesseract 路径一致）
# 如果已经配置了环境变量，可以注释掉下面这行
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 设置页面配置：宽屏模式，设置深色主题风格
st.set_page_config(
    page_title="数字化财务发票管理系统", 
    page_icon="📑", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 样式优化页面外观
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 图像增强预处理函数 ---
def preprocess_image(image):
    """通过灰度化、对比度增强和锐化提高 OCR 识别率"""
    # 转灰度
    gray_image = ImageOps.grayscale(image)
    # 增强对比度 (1.5-2.0 效果最佳)
    enhancer = ImageEnhance.Contrast(gray_image)
    gray_image = enhancer.enhance(1.8)
    # 锐化
    enhancer = ImageEnhance.Sharpness(gray_image)
    gray_image = enhancer.enhance(1.5)
    return gray_image

# --- 核心识别逻辑 ---
def extract_invoice_info(image):
    """
    实战级提取逻辑：结合多重正则匹配
    """
    processed_img = preprocess_image(image)
    # 使用简体中文和英文混合库识别
    text = pytesseract.image_to_string(processed_img, lang='chi_sim+eng')
    
    # 1. 提取金额：寻找类似 1,234.56 或 1234.56 的数字
    # 过滤掉常见的日期格式干扰
    amount_match = re.findall(r"(?:金额|合计|小写|￥|¥)\s*[:：]?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2}))", text)
    if not amount_match:
        amount_match = re.findall(r"([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2}))", text)
        
    total_amount = 0.0
    if amount_match:
        amounts = [float(a.replace(',', '')) for a in amount_match]
        total_amount = max(amounts) # 通常发票上最大的金额是含税总额

    # 2. 提取日期
    date_match = re.search(r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})", text)
    invoice_date = date_match.group(1) if date_match else "未知日期"

    # 3. 提取税率
    tax_match = re.search(r"(\d{1,2}%)", text)
    tax_rate = tax_match.group(1) if tax_match else "6%"

    # 4. 提取单位名称：识别包含关键词的行
    unit_keywords = r"([^\s\n]*(?:有限公司|股份公司|中心|集团|店|部))"
    unit_match = re.findall(unit_keywords, text)
    
    seller = "未知单位"
    buyer = "个人/默认单位"
    
    # 过滤掉过短的干扰词
    valid_units = [u for u in unit_match if len(u) > 4]
    if len(valid_units) >= 1:
        seller = valid_units[0]
    if len(valid_units) >= 2:
        buyer = valid_units[1]

    # 5. 判断发票类型
    invoice_type = "增值税普通发票"
    if any(k in text for k in ["专用", "专票", "专 用"]):
        invoice_type = "增值税专用发票"
    elif "行程单" in text:
        invoice_type = "机票行程单"

    return {
        "发票类型": invoice_type,
        "开票单位": seller,
        "受票单位": buyer,
        "总金额": total_amount,
        "税率": tax_rate,
        "日期": invoice_date
    }

# --- 页面主体设计 ---
st.title("📑 数字化财务发票识别系统")
st.caption("基于 OCR 与 Python 数据分析的自动化办公方案")

# 初始化数据存储
if 'invoice_history' not in st.session_state:
    st.session_state.invoice_history = []

# --- 侧边栏操作 ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1157/1157109.png", width=100)
    st.header("控制台")
    uploaded_files = st.file_uploader("支持批量上传 (JPG/PNG)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        process_btn = st.button("🚀 开始识别", use_container_width=True)
    with col_btn2:
        clear_btn = st.button("🗑️ 清空记录", use_container_width=True)

if clear_btn:
    st.session_state.invoice_history = []
    st.rerun()

if process_btn:
    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                # 解决输出台报错：使用 bytes 读取避免文件流关闭问题
                file_bytes = uploaded_file.read()
                image = Image.open(io.BytesIO(file_bytes))
                
                with st.spinner(f'正在解析: {uploaded_file.name}...'):
                    data = extract_invoice_info(image)
                    data['文件名'] = uploaded_file.name
                    st.session_state.invoice_history.append(data)
            except Exception as e:
                st.error(f"解析 {uploaded_file.name} 失败: {e}")
        st.success(f"处理完成！")
    else:
        st.warning("请先上传发票文件")

# --- 主展示区域 ---
# --- 数据展示与分析 ---
if st.session_state.invoice_history:
    df = pd.DataFrame(st.session_state.invoice_history)
    
    # 确保在显示图表前，数据类型是正确的
    df['总金额'] = pd.to_numeric(df['总金额'], errors='coerce').fillna(0.0)

    # 定义两个标签页
    tab1, tab2 = st.tabs(["📋 数据明细", "📊 统计报表"])
    
    with tab1:
        st.subheader("识别结果汇总与校对")
        st.info("💡 您可以直接在表格中双击修改识别错误的内容，修改后下方的图表会自动更新。")
        
        # 使用 data_editor，允许用户实时修正 OCR 的错误
        edited_df = st.data_editor(
            df, 
            column_order=['文件名', '日期', '开票单位', '受票单位', '总金额', '税率', '发票类型'],
            num_rows="dynamic", 
            use_container_width=True,
            key="invoice_editor"
        )
        
        # 导出功能
        csv = edited_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 导出为 Excel 兼容报表 (CSV)",
            data=csv,
            file_name='发票汇总报表.csv',
            mime='text/csv',
        )

    with tab2:
        # 顶部指标卡
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("发票总数", f"{len(edited_df)} 张")
        col_m2.metric("累计报销金额", f"￥{edited_df['总金额'].sum():,.2f}")
        col_m3.metric("供应商数量", f"{edited_df['开票单位'].nunique()} 家")

        st.divider()

        # 图表展示
        c1, c2 = st.columns(2)
        
        with c1:
            st.write("**支出分布（按开票单位）**")
            # 处理数据以适应柱状图
            unit_chart_data = edited_df.groupby('开票单位')['总金额'].sum().reset_index()
            if not unit_chart_data.empty:
                st.bar_chart(data=unit_chart_data, x='开票单位', y='总金额')
            else:
                st.caption("暂无足够数据生成柱状图")
        
        with c2:
            st.write("**报销类型分布**")
            # 转换数据以适应饼图/环形图
            type_count = edited_df['发票类型'].value_counts().reset_index()
            type_count.columns = ['类型', '数量']
            
            if not type_count.empty:
                # 使用 Vega-Lite 绘制更稳定的饼图
                st.vega_lite_chart(type_count, {
                    'mark': {'type': 'arc', 'innerRadius': 40},
                    'encoding': {
                        'theta': {'field': '数量', 'type': 'quantitative'},
                        'color': {'field': '类型', 'type': 'nominal'},
                    },
                }, use_container_width=True)
            else:
                st.caption("暂无足够数据生成饼图")

else:
    # 如果没有上传发票，显示欢迎界面
    st.markdown("---")
    st.info("👋 欢迎使用发票识别系统！请在左侧边栏上传发票图片，点击“开始识别”按钮。")
    st.image("https://img.freepik.com/free-vector/receipt-concept-illustration_114360-3129.jpg", width=400)

