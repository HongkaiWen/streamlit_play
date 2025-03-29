import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO

# 设置页面标题和布局
st.set_page_config(page_title="BOM 比对页面", layout="wide")
st.title("BOM 比对页面")

# 初始化会话状态
if 'selected_columns' not in st.session_state:
    st.session_state.selected_columns = {}
if 'original_bom' not in st.session_state:
    st.session_state.original_bom = None
if 'new_bom' not in st.session_state:
    st.session_state.new_bom = None

# 侧边栏用于文件上传
with st.sidebar:
    st.subheader("文件上传")
    original_bom_file = st.file_uploader("上传原版本 BOM 文件", type=["xlsx"])
    new_bom_file = st.file_uploader("上传新版本 BOM 文件", type=["xlsx"])

    if original_bom_file and new_bom_file:
        try:
            st.session_state.original_bom = pd.read_excel(original_bom_file)
            st.session_state.new_bom = pd.read_excel(new_bom_file)
            st.success("文件读取成功！")
        except Exception as e:
            st.error(f"读取文件时出现错误: {e}")

# 主内容区域
if st.session_state.original_bom is not None and st.session_state.new_bom is not None:
    # 获取共有的列名
    common_columns = list(st.session_state.original_bom.columns)

    # 物料编码列选择
    default_material = next((col for col in common_columns if "编码" in col), common_columns[0])
    material_code_column = st.selectbox("物料编码列", common_columns,
                                        index=common_columns.index(default_material))

    # 位置号列选择
    position_columns = [col for col in common_columns if col != material_code_column]
    default_position = next((col for col in position_columns if "位置号" in col), position_columns[0])
    position_number_column = st.selectbox("位置号列", position_columns,
                                          index=position_columns.index(default_position))

    # 其他列选择
    other_columns = [col for col in common_columns if col not in [material_code_column, position_number_column]]
    selected_other_columns = st.multiselect("选择其他列（可多选）", other_columns)

    # 保存选择状态到会话状态
    st.session_state.selected_columns = {
        "material": material_code_column,
        "position": position_number_column,
        "others": selected_other_columns
    }

    # 开始比对按钮
    if st.button("开始比对"):
        if not material_code_column or not position_number_column:
            st.error("物料编码列和位置号列必须选择，才能进行对比。")
        else:
            comparison_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

            # 1. 对比两个文件的物料编码
            original_material_codes = set(st.session_state.original_bom[material_code_column])
            new_material_codes = set(st.session_state.new_bom[material_code_column])
            old_diff_codes = original_material_codes - new_material_codes
            new_diff_codes = new_material_codes - original_material_codes

            material_diff_report = []
            if not old_diff_codes and not new_diff_codes:
                material_diff_report.append("物料编码没问题。")
            else:
                if old_diff_codes:
                    material_diff_report.append(
                        f"旧版本中存在但新版本中不存在的物料编码: {', '.join(map(str, old_diff_codes))}")
                if new_diff_codes:
                    material_diff_report.append(
                        f"新版本中存在但旧版本中不存在的物料编码: {', '.join(map(str, new_diff_codes))}")

            # 2. 对比相同物料编码的位置号
            merged = pd.merge(st.session_state.original_bom, st.session_state.new_bom, on=material_code_column,
                              suffixes=('_old', '_new'))
            position_diff_new_report = []
            position_diff_old_report = []
            for index, row in merged.iterrows():
                old_positions_str = row[position_number_column + '_old']
                new_positions_str = row[position_number_column + '_new']

                # 处理空值和不规范的位置号
                old_positions = set()
                new_positions = set()

                if isinstance(old_positions_str, str) and old_positions_str:
                    # 替换全角逗号并去除前后空格
                    old_positions = {pos.strip() for pos in old_positions_str.replace('，', ',').split(',') if
                                     pos.strip()}
                if isinstance(new_positions_str, str) and new_positions_str:
                    # 替换全角逗号并去除前后空格
                    new_positions = {pos.strip() for pos in new_positions_str.replace('，', ',').split(',') if
                                     pos.strip()}

                new_only_positions = new_positions - old_positions
                old_only_positions = old_positions - new_positions

                if new_only_positions:
                    position_diff_new_report.append(
                        f"物料编码 {row[material_code_column]}: {', '.join(new_only_positions)}")
                if old_only_positions:
                    position_diff_old_report.append(
                        f"物料编码 {row[material_code_column]}: {', '.join(old_only_positions)}")

            # 3. 对比其他列
            other_diff_report = []
            if selected_other_columns:
                for col in selected_other_columns:
                    for index, row in merged.iterrows():
                        old_value = row[col + '_old']
                        new_value = row[col + '_new']
                        # 检查是否两个值都是 NaN
                        if pd.isna(old_value) and pd.isna(new_value):
                            continue
                        if old_value != new_value:
                            other_diff_report.append(
                                f"物料编码 {row[material_code_column]} 的 {col} 列存在差异，旧版本值: {old_value}，新版本值: {new_value}")

            # 差异比对报告章节
            st.markdown("<h2 style='color: #007BFF;'>差异比对报告</h2>", unsafe_allow_html=True)

            # 用料差异
            st.markdown("<h3 style='color: #28a745;'>用料差异</h3>", unsafe_allow_html=True)
            for report in material_diff_report:
                st.markdown(f"<p style='color: #6c757d;'>{report}</p>", unsafe_allow_html=True)

            # 位置号差异
            st.markdown("<h3 style='color: #ffc107;'>位置号差异</h3>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #ffc107;'>新版本有而旧版本没有的位置号</h4>", unsafe_allow_html=True)
            for report in position_diff_new_report:
                st.markdown(f"<p style='color: #6c757d;'>{report}</p>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #ffc107;'>旧版本有而新版本没有的位置号</h4>", unsafe_allow_html=True)
            for report in position_diff_old_report:
                st.markdown(f"<p style='color: #6c757d;'>{report}</p>", unsafe_allow_html=True)

            # 其他选择列的差异
            if selected_other_columns:
                st.markdown("<h3 style='color: #dc3545;'>其他选择列的差异</h3>", unsafe_allow_html=True)
                for report in other_diff_report:
                    st.markdown(f"<p style='color: #6c757d;'>{report}</p>", unsafe_allow_html=True)

            # 生成 Excel 报告
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # 汇总工作表
                summary_info = [
                    f"原文件: {original_bom_file.name}",
                    f"新文件: {new_bom_file.name}",
                    f"比对时间: {comparison_time}",
                    f"物料编码列: {material_code_column}",
                    f"位置号列: {position_number_column}"
                ]
                if selected_other_columns:
                    summary_info.append(f"其他列: {', '.join(selected_other_columns)}")
                summary_df = pd.DataFrame({"比对信息": summary_info})
                summary_df.to_excel(writer, sheet_name='汇总信息', index=False)

                # 用料差异工作表
                material_diff_df = pd.DataFrame({"用料差异": material_diff_report})
                material_diff_df.to_excel(writer, sheet_name='用料差异', index=False)

                # 位置号差异工作表 - 新版本有旧版本没有
                position_diff_new_df = pd.DataFrame({"新版本有而旧版本没有的位置号差异": position_diff_new_report})
                position_diff_new_df.to_excel(writer, sheet_name='位置号差异_新版本有', index=False)

                # 位置号差异工作表 - 旧版本有新版本没有
                position_diff_old_df = pd.DataFrame({"旧版本有而新版本没有的位置号差异": position_diff_old_report})
                position_diff_old_df.to_excel(writer, sheet_name='位置号差异_旧版本有', index=False)

                # 其他选择列的差异工作表
                if selected_other_columns:
                    other_diff_df = pd.DataFrame({"其他选择列的差异": other_diff_report})
                    other_diff_df.to_excel(writer, sheet_name='其他选择列差异', index=False)

            # 获取二进制数据
            excel_bytes = output.getvalue()

            # 下载报告按钮
            st.download_button(
                label="下载差异比对报告（Excel 格式）",
                data=excel_bytes,
                file_name=f"BOM_Comparison_Report_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("请在侧边栏上传原版本 BOM 文件和新版本 BOM 文件。")
