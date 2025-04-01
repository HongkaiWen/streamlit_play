import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import locale

# 设置本地化信息，用于添加千分位逗号
locale.setlocale(locale.LC_ALL, '')

# 设置页面配置，包括标题、图标和布局
st.set_page_config(page_title='数据洞察图表生成', page_icon='📊', layout='wide')

# 自定义 CSS 样式
st.markdown("""
<style>
    /* 设置整体背景颜色 */
    body {
        background-color: #f4f4f9;
    }
    /* 设置侧边栏背景颜色 */
    .css-1d391kg {
        background-color: #eaeaf2;
    }
    /* 设置标题样式 */
    h1 {
        color: #333;
        text-align: center;
        margin-bottom: 20px;
    }
    /* 设置子标题样式 */
    h2 {
        color: #555;
        margin-top: 30px;
        margin-bottom: 10px;
    }
    /* 设置描述文字样式 */
    p {
        color: #666;
    }
    /* 设置表格样式 */
    .stDataFrame {
        border: 1px solid #ddd;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    /* 设置选择框和按钮样式 */
    .stSelectbox, .stButton {
        margin-bottom: 15px;
    }
    /* 设置文件上传器样式 */
    .stFileUploader {
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 设置页面标题
st.title('数据洞察图表生成')

# 添加页面描述
st.write("这个页面旨在帮助你对 Excel 数据进行深入的洞察分析。你可以上传一个 Excel 文件，然后选择对比维度、需要展示的指标以及指标单位，系统将为你生成相应的柱状图，展示指标按对比维度的走势。之后，你可以选择两个对比维度的值进行细化分析，选择引发变动的维度，系统将计算并展示数据的变化量、增加和减少的总额、占比等信息，帮助你深入了解数据的变化情况。")

# 上传 Excel 文件
uploaded_file = st.file_uploader("上传 Excel 文件", type=['xlsx', 'xls'])

if uploaded_file is not None:
    # 读取 Excel 文件
    df = pd.read_excel(uploaded_file)

    # 获取所有列名
    columns = df.columns.tolist()

    # 创建三列布局，用于放置选择框
    col1, col2, col3 = st.columns(3)

    # 选择对比维度
    with col1:
        selected_dimension = st.selectbox("选择对比维度", columns)

    # 选择需要展示的指标（排除已选维度）
    available_metrics = [col for col in columns if col != selected_dimension]
    preferred_metrics = [col for col in available_metrics if any(key in col for key in ["金额", "额", "量"])]
    if preferred_metrics:
        default_metric = preferred_metrics[0]
    else:
        default_metric = available_metrics[0]
    with col2:
        selected_metric = st.selectbox("选择需要展示的指标", available_metrics,
                                       index=available_metrics.index(default_metric))

    # 选择指标单位
    unit_options = ["无", "万", "百万", "亿"]
    with col3:
        selected_unit = st.selectbox("指标单位", unit_options, index=1)
    unit_multiplier = {
        "无": 1,
        "万": 10000,
        "百万": 1000000,
        "亿": 100000000
    }[selected_unit]

    aggregated_df = df.groupby(selected_dimension)[selected_metric].sum().reset_index()

    # 绘制柱状图展示指标走势并在柱子上显示数值
    fig_bar = go.Figure(data=[go.Bar(
        x=aggregated_df[selected_dimension],
        y=aggregated_df[selected_metric] / unit_multiplier,
        text=[locale.format_string('%d', val / unit_multiplier, grouping=True) for val in aggregated_df[selected_metric]],
        textposition='auto',
        marker_color='skyblue'
    )])

    fig_bar.update_layout(
        title=f'{selected_metric} 按 {selected_dimension} 的走势（单位：{selected_unit}）',
        xaxis_title=selected_dimension,
        yaxis_title=f'{selected_metric}（单位：{selected_unit}）',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#666')
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    # 选择分析维度值范围
    dimension_values = df[selected_dimension].unique().tolist()
    selected_values = st.multiselect(f"选择 {selected_dimension} 的值进行细化分析", dimension_values)

    if len(selected_values) != 2:
        st.error(f"请准确选择两个 {selected_dimension} 的值进行细化分析。")
    else:
        # 筛选数据
        filtered_df = df[df[selected_dimension].isin(selected_values)]

        # 选择引发变动的维度
        remaining_columns = [col for col in columns if col not in [selected_dimension, selected_metric]]
        causal_dimension = st.selectbox("选择引发变动的维度", remaining_columns)

        # 按引发变动的维度和选择的对比维度分组计算指标总和
        grouped = filtered_df.groupby([causal_dimension, selected_dimension])[selected_metric].sum().unstack()

        # 计算变化量
        grouped['变化量'] = grouped[selected_values[-1]] - grouped[selected_values[0]]

        # 分离增加和减少的数据
        increased = grouped[grouped['变化量'] > 0].sort_values(by='变化量', ascending=False)
        decreased = grouped[grouped['变化量'] < 0].sort_values(by='变化量')

        # 计算增加和减少的总额
        total_increase = increased['变化量'].sum() / unit_multiplier
        total_decrease = decreased['变化量'].sum() / unit_multiplier
        net_change = total_increase + total_decrease

        initial_value = filtered_df[filtered_df[selected_dimension] == selected_values[0]][
                            selected_metric].sum() / unit_multiplier
        final_value = filtered_df[filtered_df[selected_dimension] == selected_values[-1]][
                          selected_metric].sum() / unit_multiplier

        if initial_value != 0:
            net_change_percentage = net_change / initial_value * 100
        else:
            net_change_percentage = 0

        # 计算增加和减少的数量
        num_increased = len(increased)
        num_decreased = len(decreased)
        total_num = num_increased + num_decreased

        # 增加量表格优化
        if not increased.empty:
            increased['变化量（格式化）'] = increased['变化量'].apply(
                lambda x: locale.format_string('%d', x / unit_multiplier, grouping=True))
            increased['占增加总额百分比'] = (increased['变化量'] / (increased['变化量'].sum()) * 100).map(
                '{:.2f}%'.format)
            increased['累计增加额百分比'] = (increased['变化量'].cumsum() / (increased['变化量'].sum()) * 100).map(
                '{:.2f}%'.format)
            increased['增加前的量'] = (increased[selected_values[0]] / unit_multiplier).apply(
                lambda x: locale.format_string('%d', x, grouping=True))
            increased['增加后的量'] = (increased[selected_values[-1]] / unit_multiplier).apply(
                lambda x: locale.format_string('%d', x, grouping=True))

        # 减少量表格优化
        if not decreased.empty:
            decreased['变化量（格式化）'] = decreased['变化量'].apply(
                lambda x: locale.format_string('%d', x / unit_multiplier, grouping=True))
            decreased['占减少总额百分比'] = (decreased['变化量'] / (decreased['变化量'].sum()) * 100).map(
                '{:.2f}%'.format)
            decreased['累计减少额百分比'] = (decreased['变化量'].cumsum() / (decreased['变化量'].sum()) * 100).map(
                '{:.2f}%'.format)
            decreased['减少前的量'] = (decreased[selected_values[0]] / unit_multiplier).apply(
                lambda x: locale.format_string('%d', x, grouping=True))
            decreased['减少后的量'] = (decreased[selected_values[-1]] / unit_multiplier).apply(
                lambda x: locale.format_string('%d', x, grouping=True))

        # 显示增加的数据表格描述
        st.subheader(f'{causal_dimension} 维度下 {selected_metric} 数据变化情况（单位：{selected_unit}）')
        change_verb = "增加" if net_change > 0 else "减少" if net_change < 0 else "无变化"
        description = f'从 {selected_values[0]} 到 {selected_values[1]}，{selected_metric} 从 {locale.format_string("%d", initial_value, grouping=True)} {change_verb} 到 {locale.format_string("%d", final_value, grouping=True)}，{change_verb} 量为 {locale.format_string("%d", abs(net_change), grouping=True)}，{change_verb} 比例为 {abs(net_change_percentage):.2f}%；'
        description += f'共涉及 {total_num} 个 {causal_dimension}，其中 {selected_metric} 增加的 {causal_dimension} 有 {num_increased} 个，共增加了 {locale.format_string("%d", total_increase, grouping=True)}；{selected_metric} 减少的有 {num_decreased} 个，共减少了 {locale.format_string("%d", abs(total_decrease), grouping=True)}。'
        st.write(description)


        def color_cumulative_percentage(row):
            try:
                value = float(row['累计增加百分比' if '累计增加百分比' in row.index else '累计减少百分比'].rstrip('%'))
                if 0 <= value <= 80:
                    return ['background-color: #E6E6FA'] * len(row)
                elif 80 < value <= 90:
                    return ['background-color: #FFFFCC'] * len(row)
                else:
                    return [''] * len(row)
            except ValueError:
                return [''] * len(row)


        # 显示增加的数据表格
        st.subheader(f'{causal_dimension} 维度下 {selected_metric} 增加的数据（从大到小排序）')
        if not increased.empty:
            increased_display = increased[
                ['增加前的量', '增加后的量', '变化量（格式化）', '占增加总额百分比', '累计增加额百分比']]
            increased_display.columns = ['增加前的量', '增加后的量', '增加量', '占增加总额百分比', '累计增加百分比']
            styled_increased = increased_display.style.apply(color_cumulative_percentage, axis=1)
            st.dataframe(styled_increased, use_container_width=True)
        else:
            st.write('无增加的数据')

        # 显示减少的数据表格
        st.subheader(f'{causal_dimension} 维度下 {selected_metric} 减少的数据（从多到少排序）')
        if not decreased.empty:
            decreased_display = decreased[
                ['减少前的量', '减少后的量', '变化量（格式化）', '占减少总额百分比', '累计减少额百分比']]
            decreased_display.columns = ['减少前的量', '减少后的量', '减少量', '占减少总额百分比', '累计减少百分比']
            styled_decreased = decreased_display.style.apply(color_cumulative_percentage, axis=1)
            st.dataframe(styled_decreased, use_container_width=True)
        else:
            st.write('无减少的数据')