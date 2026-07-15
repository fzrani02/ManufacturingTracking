import streamlit as st
import pandas as pd
import io

# =====================================================================
# FUNGSI PEMBANTU UNTUK KUSTOMISASI WARNA/STYLE DI STREAMLIT
# =====================================================================
def style_model_dataframe(df):
    def style_cells(x):
        df_style = pd.DataFrame('', index=x.index, columns=x.columns)
        for i in range(len(x)):
            is_yield = x['Metric'].iloc[i] == 'Yield'
            for j, col in enumerate(x.columns):
                styles = []
                
                if col in ['Q1', 'Q2', 'Q3', 'Q4']:
                    styles.append('background-color: #CFE2F3') 
                
                if col.startswith('WW'):
                    styles.append('color: #00008B') 
                else:
                    styles.append('color: #000000')

                if is_yield:
                    styles.append('border-bottom: 2px solid #000000')
                    
                df_style.iloc[i, j] = '; '.join(styles)
        return df_style

    styler = df.style.apply(style_cells, axis=None)
    styler.set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#CFE2F3'), ('font-weight', 'bold'), ('color', 'black'), ('border', '1px solid white')]}
    ])
    
    return styler

# =====================================================================
# FUNGSI PEMBANTU UNTUK MEMBANGUN TABEL PER STATION & MODEL
# =====================================================================
def build_model_yield_dataframe(target_station, df_qty_raw, df_w_raw, yy, year_str):
    final_rows = []
    
    q1_months = ["Jan", "Feb", "Mar"]
    q2_months = ["Apr", "May", "Jun"]
    q3_months = ["Jul", "Aug", "Sep"]
    q4_months = ["Oct", "Nov", "Dec"]
    all_months = q1_months + q2_months + q3_months + q4_months
    all_weeks = [f"WW{str(i).zfill(2)}" for i in range(1, 54)]
    
    # Filter data hanya untuk Station yang diminta
    df_m = df_qty_raw[df_qty_raw["Station"] == target_station].copy()
    df_w = df_w_raw[df_w_raw["Station"] == target_station].copy()
    
    if df_m.empty:
        return pd.DataFrame()
        
    # Bersihkan nama Project agar menjadi nama Model yang rapi
    df_m["Project"] = df_m["Project"].astype(str).str.replace(".xlsx", "", regex=False)
    df_w["Project"] = df_w["Project"].astype(str).str.replace(".xlsx", "", regex=False)
    
    # Dapatkan kombinasi unik Customer dan Model
    unique_combos = df_m[["Customer", "Project"]].drop_duplicates().sort_values(by=["Customer", "Project"])
    
    # Fungsi kecil untuk menarik angka dengan aman dari format df_qty yang menyamping
    def get_qty_val(df_source, time_col, qty_keyword):
        if time_col not in df_source.columns:
            return 0
        rows = df_source[df_source["QTY"].astype(str).str.contains(qty_keyword, case=False, na=False)]
        return pd.to_numeric(rows[time_col], errors='coerce').fillna(0).sum()
    
    for _, combo in unique_combos.iterrows():
        cust = combo["Customer"]
        proj = combo["Project"]
        
        m_data = df_m[(df_m["Customer"] == cust) & (df_m["Project"] == proj)]
        w_data = df_w[(df_w["Customer"] == cust) & (df_w["Project"] == proj)]
        
        tested, passed, rejected = {}, {}, {}
        
        # Ekstrak data bulanan menyamping
        for m in all_months:
            tested[m] = get_qty_val(m_data, m, "IN")
            passed[m] = get_qty_val(m_data, m, "PASS")
            rejected[m] = get_qty_val(m_data, m, "FAIL")
            
        # Ekstrak data mingguan menyamping
        for w in all_weeks:
            tested[w] = get_qty_val(w_data, w, "IN")
            passed[w] = get_qty_val(w_data, w, "PASS")
            rejected[w] = get_qty_val(w_data, w, "FAIL")
            
        # Kalkulasi Kuartal
        for q, q_months in zip(["Q1", "Q2", "Q3", "Q4"], [q1_months, q2_months, q3_months, q4_months]):
            tested[q] = sum(tested[m] for m in q_months)
            passed[q] = sum(passed[m] for m in q_months)
            rejected[q] = sum(rejected[m] for m in q_months)
            
        # Kalkulasi YTD
        tested["YTD"] = sum(tested[m] for m in all_months)
        passed["YTD"] = sum(passed[m] for m in all_months)
        rejected["YTD"] = sum(rejected[m] for m in all_months)
        
        def create_metric_row(metric_name, data_dict, is_yield=False):
            # Tampilkan nama Customer & Model HANYA di baris 'Total qty tested'
            row = {
                "Metric": metric_name, 
                "CUSTOMER": cust if metric_name == "Total qty tested" else "",
                "MODEL": proj if metric_name == "Total qty tested" else ""
            }
            
            def get_val(key):
                if not is_yield:
                    return int(data_dict.get(key, 0))
                else:
                    t = tested.get(key, 0)
                    p = passed.get(key, 0)
                    return f"{(p/t)*100:.2f}%" if t > 0 else "0%"
            
            # --- SUSUNAN KOLOM ---
            row[f"JAN'{yy}"] = get_val("Jan")
            for w in [f"WW{str(i).zfill(2)}" for i in range(1, 5)]: row[w] = get_val(w)
            row[f"FEB'{yy}"] = get_val("Feb")
            for w in [f"WW{str(i).zfill(2)}" for i in range(5, 9)]: row[w] = get_val(w)
            row[f"MAR'{yy}"] = get_val("Mar")
            for w in [f"WW{str(i).zfill(2)}" for i in range(9, 14)]: row[w] = get_val(w)
            row["Q1"] = get_val("Q1")
            
            row[f"APR'{yy}"] = get_val("Apr")
            for w in [f"WW{str(i).zfill(2)}" for i in range(14, 18)]: row[w] = get_val(w)
            row[f"MAY'{yy}"] = get_val("May")
            for w in [f"WW{str(i).zfill(2)}" for i in range(18, 22)]: row[w] = get_val(w)
            row[f"JUN'{yy}"] = get_val("Jun")
            for w in [f"WW{str(i).zfill(2)}" for i in range(22, 27)]: row[w] = get_val(w)
            row["Q2"] = get_val("Q2")
            
            row[f"JUL'{yy}"] = get_val("Jul")
            for w in [f"WW{str(i).zfill(2)}" for i in range(27, 31)]: row[w] = get_val(w)
            row[f"AUG'{yy}"] = get_val("Aug")
            for w in [f"WW{str(i).zfill(2)}" for i in range(31, 35)]: row[w] = get_val(w)
            row[f"SEP'{yy}"] = get_val("Sep")
            for w in [f"WW{str(i).zfill(2)}" for i in range(35, 39)]: row[w] = get_val(w)
            row["Q3"] = get_val("Q3")
            
            row[f"OCT'{yy}"] = get_val("Oct")
            for w in [f"WW{str(i).zfill(2)}" for i in range(39, 44)]: row[w] = get_val(w)
            row[f"NOV'{yy}"] = get_val("Nov")
            for w in [f"WW{str(i).zfill(2)}" for i in range(44, 48)]: row[w] = get_val(w)
            row[f"DEC'{yy}"] = get_val("Dec")
            for w in [f"WW{str(i).zfill(2)}" for i in range(48, 54)]: row[w] = get_val(w)
            row["Q4"] = get_val("Q4")
            
            row[f"{year_str} YTD"] = get_val("YTD")
            
            return row

        final_rows.append(create_metric_row("Total qty tested", tested, is_yield=False))
        final_rows.append(create_metric_row("Total qty passed", passed, is_yield=False))
        final_rows.append(create_metric_row("Total qty rejected", rejected, is_yield=False))
        final_rows.append(create_metric_row("Yield", None, is_yield=True))
        
    return pd.DataFrame(final_rows)

# =====================================================================
# FUNGSI UTAMA RENDER TAB MODEL REPORT
# =====================================================================
def render_tab_model_report(df_qty_raw, df_qty_weekly_raw, extracted_year):
    st.header("🗃️ Report by Model for ICT, BT, and FCT Customer")
    
    year_str = str(extracted_year) if extracted_year else "2026"
    yy = year_str[-2:]
    
    # --- PREPROCESSING GLOBAL ---
    df_qty = df_qty_raw.copy()
    df_qty_weekly = df_qty_weekly_raw.copy()
    
    df_qty["Customer"] = df_qty["Customer"].astype(str).str.upper().str.strip()
    df_qty["Station"] = df_qty["Station"].astype(str).str.upper().str.strip()
    
    df_qty_weekly["Customer"] = df_qty_weekly["Customer"].astype(str).str.upper().str.strip()
    df_qty_weekly["Station"] = df_qty_weekly["Station"].astype(str).str.upper().str.strip()

    # 1. FCT YIELD PER MODEL
    st.subheader(f"FCT Yield ALL FY{yy} per Model")
    df_fct_model = build_model_yield_dataframe("FCT", df_qty, df_qty_weekly, yy, year_str)
    if not df_fct_model.empty:
        st.dataframe(style_model_dataframe(df_fct_model), use_container_width=True, hide_index=True)
    else:
        st.info("Not available.")

    # 2. ICT YIELD PER MODEL
    st.markdown("---")
    st.subheader(f"ICT Yield ALL FY{yy} per Model")
    df_ict_model = build_model_yield_dataframe("ICT", df_qty, df_qty_weekly, yy, year_str)
    if not df_ict_model.empty:
        st.dataframe(style_model_dataframe(df_ict_model), use_container_width=True, hide_index=True)
    else:
        st.info("Not available.")

    # 3. BLT YIELD PER MODEL
    st.markdown("---")
    st.subheader(f"BLT Yield ALL FY{yy} per Model")
    df_blt_model = build_model_yield_dataframe("BLT", df_qty, df_qty_weekly, yy, year_str)
    if not df_blt_model.empty:
        st.dataframe(style_model_dataframe(df_blt_model), use_container_width=True, hide_index=True)
    else:
        st.info("Not available.")

    # ==================================
    # EXPORT KE EXCEL
    # ==================================
    st.markdown("---")
    excel_buffer = io.BytesIO()
    
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        fmt_header_month = workbook.add_format({'bg_color': '#CFE2F3', 'bold': True, 'font_color': '#000000', 'border': 1, 'align': 'center'})
        fmt_header_ww = workbook.add_format({'bg_color': '#CFE2F3', 'bold': True, 'font_color': '#00008B', 'border': 1, 'align': 'center'})
        fmt_q = workbook.add_format({'bg_color': '#CFE2F3'})
        fmt_ww = workbook.add_format({'font_color': '#00008B'})
        
        fmt_yield = workbook.add_format({'bottom': 1})
        fmt_yield_ww = workbook.add_format({'bottom': 1, 'font_color': '#00008B'})
        fmt_yield_q = workbook.add_format({'bottom': 1, 'bg_color': '#CFE2F3'})
        
        reports_dict = {
            'FCT': df_fct_model,
            'ICT': df_ict_model,
            'BLT': df_blt_model
        }
        
        for sheet_name, df_report in reports_dict.items():
            if df_report.empty:
                continue
                
            df_report.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            
            for col_num, col_name in enumerate(df_report.columns):
                if col_name.startswith('WW'):
                    worksheet.write(0, col_num, col_name, fmt_header_ww)
                else:
                    worksheet.write(0, col_num, col_name, fmt_header_month)
                    
            for col_num, col_name in enumerate(df_report.columns):
                if col_name in ['Metric', 'CUSTOMER', 'MODEL']:
                    worksheet.set_column(col_num, col_num, 16)
                elif col_name in ['Q1', 'Q2', 'Q3', 'Q4']:
                    worksheet.set_column(col_num, col_num, 10, fmt_q)
                elif col_name.startswith('WW'):
                    worksheet.set_column(col_num, col_num, 9, fmt_ww)
                else:
                    worksheet.set_column(col_num, col_num, 10)
                    
            for row_num in range(len(df_report)):
                if df_report.iloc[row_num]['Metric'] == 'Yield':
                    for col_num, col_name in enumerate(df_report.columns):
                        val = df_report.iloc[row_num, col_num]
                        if col_name in ['Q1', 'Q2', 'Q3', 'Q4']:
                            worksheet.write(row_num + 1, col_num, val, fmt_yield_q)
                        elif col_name.startswith('WW'):
                            worksheet.write(row_num + 1, col_num, val, fmt_yield_ww)
                        else:
                            worksheet.write(row_num + 1, col_num, val, fmt_yield)
    
    st.download_button(
        label=f"📥 Download Yield ALL FY{yy} per Model",
        data=excel_buffer.getvalue(),
        file_name="Life Fitness Overall Yield Summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
