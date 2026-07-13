import streamlit as st
import pandas as pd
import io # Pastikan ini di-import untuk membuat file excel di memori

# =====================================================================
# FUNGSI PEMBANTU UNTUK MEMBANGUN STRUKTUR TABEL
# =====================================================================
def build_yield_dataframe(target_customers, df_m_agg, df_w_agg, yy, year_str):
    final_rows = []
    
    q1_months = ["Jan", "Feb", "Mar"]
    q2_months = ["Apr", "May", "Jun"]
    q3_months = ["Jul", "Aug", "Sep"]
    q4_months = ["Oct", "Nov", "Dec"]
    all_months = q1_months + q2_months + q3_months + q4_months
    
    all_weeks = [f"WW{str(i).zfill(2)}" for i in range(1, 54)]
    
    for cust in target_customers:
        m_data = df_m_agg[df_m_agg["Customer"] == cust]
        w_data = df_w_agg[df_w_agg["Customer"] == cust]
        
        tested, passed, rejected = {}, {}, {}
        
        # Isi data bulanan
        for m in all_months:
            row_m = m_data[m_data["Month"] == m]
            tested[m] = row_m["TOTAL QTY IN"].sum() if not row_m.empty else 0
            passed[m] = row_m["TOTAL QTY PASS"].sum() if not row_m.empty else 0
            rejected[m] = row_m["TOTAL QTY FAIL"].sum() if not row_m.empty else 0
            
        # Isi data mingguan
        for w in all_weeks:
            row_w = w_data[w_data["Week"] == w]
            tested[w] = row_w["TOTAL QTY IN"].sum() if not row_w.empty else 0
            passed[w] = row_w["TOTAL QTY PASS"].sum() if not row_w.empty else 0
            rejected[w] = row_w["TOTAL QTY FAIL"].sum() if not row_w.empty else 0
            
        # Kalkulasi Kuartal
        tested["Q1"] = sum(tested[m] for m in q1_months)
        passed["Q1"] = sum(passed[m] for m in q1_months)
        rejected["Q1"] = sum(rejected[m] for m in q1_months)
        
        tested["Q2"] = sum(tested[m] for m in q2_months)
        passed["Q2"] = sum(passed[m] for m in q2_months)
        rejected["Q2"] = sum(rejected[m] for m in q2_months)
        
        tested["Q3"] = sum(tested[m] for m in q3_months)
        passed["Q3"] = sum(passed[m] for m in q3_months)
        rejected["Q3"] = sum(rejected[m] for m in q3_months)
        
        tested["Q4"] = sum(tested[m] for m in q4_months)
        passed["Q4"] = sum(passed[m] for m in q4_months)
        rejected["Q4"] = sum(rejected[m] for m in q4_months)
        
        # Kalkulasi YTD
        tested["YTD"] = sum(tested[m] for m in all_months)
        passed["YTD"] = sum(passed[m] for m in all_months)
        rejected["YTD"] = sum(rejected[m] for m in all_months)
        
        def create_metric_row(metric_name, data_dict, is_yield=False):
            row = {"Metric": metric_name, "CUSTOMER": cust if metric_name == "Total qty tested" else ""}
            
            def get_val(key):
                if not is_yield:
                    return int(data_dict.get(key, 0))
                else:
                    t = tested.get(key, 0)
                    p = passed.get(key, 0)
                    # Handle jika tidak ada data agar tidak error
                    return f"{(p/t)*100:.2f}%" if t > 0 else "#DIV/0!"
            
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
# FUNGSI UTAMA RENDER TAB REPORT
# =====================================================================
def render_tab_report(df_qty, df_fail, df_monthly, df_qty_weekly, df_fail_weekly, df_weekly_detail, extracted_year):
    st.header("Report Tab")
    
    year_str = str(extracted_year) if extracted_year else "2026"
    yy = year_str[-2:]
    
    # --- PREPROCESSING GLOBAL ---
    # Agar aman dari huruf besar/kecil & spasi ekstra
    df_m = df_monthly.copy()
    df_m["Customer"] = df_m["Customer"].astype(str).str.upper().str.strip()
    df_m_agg = df_m.groupby(["Customer", "Month"], as_index=False)[["TOTAL QTY IN", "TOTAL QTY PASS", "TOTAL QTY FAIL"]].sum()
    
    df_w = df_weekly_detail.copy()
    df_w["Customer"] = df_w["Customer"].astype(str).str.upper().str.strip()
    df_w_agg = df_w.groupby(["Customer", "Week"], as_index=False)[["TOTAL QTY IN", "TOTAL QTY PASS", "TOTAL QTY FAIL"]].sum()

    # ==================================
    # 1. ICT YIELD
    # ==================================
    st.subheader(f"1. ICT Yield ALL FY{yy}")
    target_ict = [
        "COGNEX ICT", "GEA", "LIFE FITNESS", "PITNEY BOWES", "REGAL BELOIT", 
        "TECUMSEH", "ABB", "HP", "SLEEP NUMBER", "WEBER", "NOVANTA", 
        "EROAD", "BRANE AUDIO", "CAT", "GDI", "PRO1"
    ]
    df_ict_report = build_yield_dataframe(target_ict, df_m_agg, df_w_agg, yy, year_str)
    st.dataframe(df_ict_report, use_container_width=True, hide_index=True)


    # ==================================
    # 2. BT YIELD
    # ==================================
    st.markdown("---")
    st.subheader(f"2. BT Yield ALL FY{yy}")
    target_bt = [
        "GEA", "LIFE FITNESS", "GDI", "REGAL BELOIT", "TRANE JOLT", 
        "ABB", "HP", "SLEEP NUMBER", "WEBER", "PITNEY BOWES", 
        "TELEMATICS", "EROAD", "SECURUS", "BRANE AUDIO", "ORBCOMM", 
        "DATA LOGIC", "SEEING MACHINE", "CARRIER TRANSICOLD", "NOVANTA", 
        "LMI", "PRO1"
    ]
    df_bt_report = build_yield_dataframe(target_bt, df_m_agg, df_w_agg, yy, year_str)
    st.dataframe(df_bt_report, use_container_width=True, hide_index=True)
    
    
    # ==================================
    # 3. FCT YIELD
    # ==================================
    st.markdown("---")
    st.subheader(f"3. FCT Yield ALL FY{yy}")
    target_fct = [
        "COGNEX", "GEA", "LIFE FITNESS", "PITNEY BOWES", "GDI", 
        "REGAL BELOIT", "TECUMSEH", "ABB", "HP", "TRANE JOLT", 
        "SLEEP NUMBER", "WEBER", "TELEMATICS", "NPE", "ORBCOMM", 
        "SECURUS", "EROAD", "BRANE AUDIO", "EVIDENT", "DATA LOGIC", 
        "SEEING MACHINE", "GEHC", "CARRIER TRANSICOLD", "VIDEOJET", 
        "LMI", "PRO1"
    ]
    df_fct_report = build_yield_dataframe(target_fct, df_m_agg, df_w_agg, yy, year_str)
    st.dataframe(df_fct_report, use_container_width=True, hide_index=True)


    # ==================================
    # EXPORT KE EXCEL
    # ==================================
    st.markdown("---")
    
    # Membuat buffer memori untuk file Excel
    excel_buffer = io.BytesIO()
    
    # Menulis ke-3 DataFrame ke dalam satu file Excel dengan sheet yang berbeda
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df_ict_report.to_excel(writer, sheet_name=f'ICT Yield ALL FY{yy}', index=False)
        df_bt_report.to_excel(writer, sheet_name=f'BT Yield ALL FY{yy}', index=False)
        df_fct_report.to_excel(writer, sheet_name=f'FCT Yield ALL FY{yy}', index=False)
    
    # Tombol Download Streamlit
    st.download_button(
        label="📥 Export to Excel (RTY-ICT-BT-FCT -Overall)",
        data=excel_buffer.getvalue(),
        file_name="RTY-ICT-BT-FCT -Overall.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
