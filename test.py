import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def create_waterfall_chart(df_original, start_end_dim, start_val, end_val, second_dim, indicator):
    # 筛选起始和结束的数据
    start_value = df_original[df_original[start_end_dim] == start_val][indicator].sum()
    end_value = df_original[df_original[start_end_dim] == end_val][indicator].sum()

    # 筛选中间上升和下降的数据
    middle_df = df_original[~df_original[start_end_dim].isin([start_val, end_val])]
    middle_values = middle_df.groupby(second_dim)[indicator].sum()

    # 组合数据
    categories = [start_val] + list(middle_values.index) + [end_val]
    values = [start_value] + list(middle_values) + [end_value - start_value - middle_values.sum()]

    df = pd.DataFrame({
        'Category': categories,
        'Value': values
    })

    # 定义颜色列表
    colors = ['blue']  # 起始值的颜色
    for value in df['Value'][1:-1]:  # 中间值的颜色
        if value > 0:
            colors.append('green')
        else:
            colors.append('red')
    colors.append('purple')  # 结束值的颜色

    # 生成 Plotly 瀑布图
    fig = go.Figure(go.Waterfall(
        name="Waterfall",
        x=df['Category'],
        y=df['Value'],
        measure=["absolute"] + ["relative"] * (len(df) - 2) + ["total"],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        textposition="outside",
        text=df['Value'],
        increasing={"marker": {"color": "green"}},
        decreasing={"marker": {"color": "red"}},
        totals={"marker": {"color": "purple"}}
    ))

    # 为每个柱子设置颜色
    fig.update_traces(marker_color=colors)

    fig.update_layout(
        title=f"Waterfall Chart - {indicator}",
        xaxis_title=start_end_dim,
        yaxis_title=indicator,
        height=500,
        margin=dict(t=50, b=50, l=50, r=50),
        autosize=True
    )

    return fig

# 读取 Excel 文件
df_original = pd.read_excel('C:\\Users\\hongkai.wen\\Downloads\\20200101-20250201汽车车销量.xlsx')

# 创建瀑布图
fig = create_waterfall_chart(df_original, "年份", "2023", "2024", "售价（万元）", "销量")

# 在 Streamlit 中显示图表
st.title("Waterfall Chart in Streamlit")
st.plotly_chart(fig)