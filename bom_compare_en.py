import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO

# Set page title and layout
st.set_page_config(page_title="BOM Comparison Page", layout="wide")
st.title("BOM Comparison Page")

# Initialize session state
if 'selected_columns' not in st.session_state:
    st.session_state.selected_columns = {}
if 'original_bom' not in st.session_state:
    st.session_state.original_bom = None
if 'new_bom' not in st.session_state:
    st.session_state.new_bom = None

# Sidebar for file upload
with st.sidebar:
    st.subheader("File Upload")
    original_bom_file = st.file_uploader("Upload the original BOM file", type=["xlsx"])
    new_bom_file = st.file_uploader("Upload the new BOM file", type=["xlsx"])

    if original_bom_file and new_bom_file:
        try:
            st.session_state.original_bom = pd.read_excel(original_bom_file)
            st.session_state.new_bom = pd.read_excel(new_bom_file)
            st.success("Files read successfully!")
        except Exception as e:
            st.error(f"An error occurred while reading the files: {e}")

# Main content area
if st.session_state.original_bom is not None and st.session_state.new_bom is not None:
    # Get common column names
    common_columns = list(st.session_state.original_bom.columns)

    # Material code column selection
    def find_default_column(columns, keywords):
        for keyword in keywords:
            for col in columns:
                if keyword.lower() in col.lower():
                    return col
        return columns[0]

    default_material_keywords = ["code", "number"]
    default_material = find_default_column(common_columns, default_material_keywords)
    material_code_column = st.selectbox("Material Code Column", common_columns,
                                        index=common_columns.index(default_material))

    # Position number column selection
    position_columns = [col for col in common_columns if col != material_code_column]
    default_position_keywords = ["position"]
    default_position = find_default_column(position_columns, default_position_keywords)
    position_number_column = st.selectbox("Position Number Column", position_columns,
                                          index=position_columns.index(default_position))

    # Other column selection
    other_columns = [col for col in common_columns if col not in [material_code_column, position_number_column]]
    selected_other_columns = st.multiselect("Select other columns (multiple selection allowed)", other_columns)

    # Save selection state to session state
    st.session_state.selected_columns = {
        "material": material_code_column,
        "position": position_number_column,
        "others": selected_other_columns
    }

    # Start comparison button
    if st.button("Start Comparison"):
        if not material_code_column or not position_number_column:
            st.error("Material code column and position number column must be selected for comparison.")
        else:
            comparison_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

            # 1. Compare material codes in two files
            original_material_codes = set(st.session_state.original_bom[material_code_column])
            new_material_codes = set(st.session_state.new_bom[material_code_column])
            old_diff_codes = original_material_codes - new_material_codes
            new_diff_codes = new_material_codes - original_material_codes

            material_diff_report = []
            if not old_diff_codes and not new_diff_codes:
                material_diff_report.append("Material codes are okay.")
            else:
                if old_diff_codes:
                    material_diff_report.append(
                        f"Material codes present in the old version but not in the new version: {', '.join(map(str, old_diff_codes))}")
                if new_diff_codes:
                    material_diff_report.append(
                        f"Material codes present in the new version but not in the old version: {', '.join(map(str, new_diff_codes))}")

            # 2. Compare position numbers of the same material codes
            merged = pd.merge(st.session_state.original_bom, st.session_state.new_bom, on=material_code_column,
                              suffixes=('_old', '_new'))
            position_diff_new_report = []
            position_diff_old_report = []
            for index, row in merged.iterrows():
                old_positions_str = row[position_number_column + '_old']
                new_positions_str = row[position_number_column + '_new']

                # Handle null values and irregular position numbers
                old_positions = set()
                new_positions = set()

                if isinstance(old_positions_str, str) and old_positions_str:
                    # Replace full-width commas and remove leading and trailing spaces
                    old_positions = {pos.strip() for pos in old_positions_str.replace('，', ',').split(',') if
                                     pos.strip()}
                if isinstance(new_positions_str, str) and new_positions_str:
                    # Replace full-width commas and remove leading and trailing spaces
                    new_positions = {pos.strip() for pos in new_positions_str.replace('，', ',').split(',') if
                                     pos.strip()}

                new_only_positions = new_positions - old_positions
                old_only_positions = old_positions - new_positions

                if new_only_positions:
                    position_diff_new_report.append(
                        f"Material code {row[material_code_column]}: {', '.join(new_only_positions)}")
                if old_only_positions:
                    position_diff_old_report.append(
                        f"Material code {row[material_code_column]}: {', '.join(old_only_positions)}")

            # 3. Compare other columns
            other_diff_report = []
            if selected_other_columns:
                for col in selected_other_columns:
                    for index, row in merged.iterrows():
                        old_value = row[col + '_old']
                        new_value = row[col + '_new']
                        # Check if both values are NaN
                        if pd.isna(old_value) and pd.isna(new_value):
                            continue
                        if old_value != new_value:
                            other_diff_report.append(
                                f"Column {col} of material code {row[material_code_column]} has differences. Old value: {old_value}, New value: {new_value}")

            # Difference comparison report section
            st.markdown("<h2 style='color: #007BFF;'>Difference Comparison Report</h2>", unsafe_allow_html=True)

            # Material usage differences
            st.markdown("<h3 style='color: #28a745;'>Material Usage Differences</h3>", unsafe_allow_html=True)
            for report in material_diff_report:
                st.markdown(f"<p style='color: #6c757d;'>{report}</p>", unsafe_allow_html=True)

            # Position number differences
            st.markdown("<h3 style='color: #ffc107;'>Position Number Differences</h3>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #ffc107;'>Position numbers present in the new version but not in the old version</h4>", unsafe_allow_html=True)
            for report in position_diff_new_report:
                st.markdown(f"<p style='color: #6c757d;'>{report}</p>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #ffc107;'>Position numbers present in the old version but not in the new version</h4>", unsafe_allow_html=True)
            for report in position_diff_old_report:
                st.markdown(f"<p style='color: #6c757d;'>{report}</p>", unsafe_allow_html=True)

            # Differences in other selected columns
            if selected_other_columns:
                st.markdown("<h3 style='color: #dc3545;'>Differences in Other Selected Columns</h3>", unsafe_allow_html=True)
                for report in other_diff_report:
                    st.markdown(f"<p style='color: #6c757d;'>{report}</p>", unsafe_allow_html=True)

            # Generate Excel report
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Summary worksheet
                summary_info = [
                    f"Original file: {original_bom_file.name}",
                    f"New file: {new_bom_file.name}",
                    f"Comparison time: {comparison_time}",
                    f"Material code column: {material_code_column}",
                    f"Position number column: {position_number_column}"
                ]
                if selected_other_columns:
                    summary_info.append(f"Other columns: {', '.join(selected_other_columns)}")
                summary_df = pd.DataFrame({"Comparison Information": summary_info})
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

                # Material usage differences worksheet
                material_diff_df = pd.DataFrame({"Material Usage Differences": material_diff_report})
                material_diff_df.to_excel(writer, sheet_name='Material Diff', index=False)

                # Position number differences worksheet - New version has but old version doesn't
                position_diff_new_df = pd.DataFrame({"Position Numbers in New Version but not in Old Version": position_diff_new_report})
                position_diff_new_df.to_excel(writer, sheet_name='Pos Diff - New', index=False)

                # Position number differences worksheet - Old version has but new version doesn't
                position_diff_old_df = pd.DataFrame({"Position Numbers in Old Version but not in New Version": position_diff_old_report})
                position_diff_old_df.to_excel(writer, sheet_name='Pos Diff - Old', index=False)

                # Differences in other selected columns worksheet
                if selected_other_columns:
                    other_diff_df = pd.DataFrame({"Differences in Other Selected Columns": other_diff_report})
                    other_diff_df.to_excel(writer, sheet_name='Other Diff', index=False)

            # Get binary data
            excel_bytes = output.getvalue()

            # Download report button
            st.download_button(
                label="Download Difference Comparison Report (Excel format)",
                data=excel_bytes,
                file_name=f"BOM_Comparison_Report_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("Please upload the original BOM file and the new BOM file in the sidebar.")