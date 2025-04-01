import pandas as pd
import locale

# 设置本地化信息，用于添加千分位逗号
locale.setlocale(locale.LC_ALL, '')

# 创建一个示例 DataFrame
data = {
    '销售额': [1234567, 2345678, 3456789]
}
df = pd.DataFrame(data)

selected_metric = '销售额'
unit_multiplier = 10000

# 使用列表推导式进行格式化
formatted_values = [locale.format_string('%d', val / unit_multiplier, grouping=True) for val in df[selected_metric]]

print(formatted_values)