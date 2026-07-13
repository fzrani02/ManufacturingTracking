import streamlit as st
import pandas as pd
import numpy as np

def render_tab_report(df_qty, df_fail, df_monthly, df_qty_weekly, df_fail_weekly, df_weekly_detail, extracted_year):
    st.header("Report Tab")
    
    # -------------------------------------------------------------
    # 1. PERSIAPAN VARIABEL TAHUN & CUSTOMER
    # -------------------------------------------------------------
    year_str = str(extracted_year) if extracted_year else "2026"
    yy = year_str[-2:] # Ambil 2 digit terakhir, misal '26'
    
    st.subheader(f"ICT Yield ALL FY{yy}")
    
    # Daftar customer spesifik untuk tabel ICT
    target_customers = [
        "COGNEX ICT", "GEA", "LIFE FITNESS", "PITNEY BOWES", "REGAL BELOIT", 
        "TECUMSEH", "ABB", "HP", "SLEEP NUMBER", "WEBER", "NOVANTA", 
        "EROAD", "BRANE AUDIO", "CAT", "GDI", "PRO1"
    ]
    
    # -------------------------------------------------------------
    # 2. FILTER & AGREGASI DATA BULANAN
    # -------------------------------------------------------------
    # Filter data bulanan sesuai target customer
    df_m = df_monthly[df_monthly["Customer"].isin(target_customers)].copy()
    
    # Agregasi (Sum) berdasarkan Customer dan Bulan (Abaikan Station/Project)
    df_m_agg = df_m.groupby(["Customer", "Month"], as_index=False)[
        ["TOTAL QTY IN", "TOTAL QTY PASS", "TOTAL QTY FAIL"]
    ].sum()
    
    # Mapping nama bulan di data ke format header (misal: "Jan" -> "JAN'26")
    month_map = {
        "Jan": f"JAN'{yy}", "Feb": f"FEB'{yy}", "Mar": f"MAR'{yy}",
        "Apr": f"APR'{yy}", "May": f"MAY'{yy}", "Jun": f"JUN'{yy}",
        "Jul": f"JUL'{yy}", "Aug": f"AUG'{yy}", "Sep": f"SEP'{yy}",
        "Oct": f"OCT'{yy}", "Nov": f"NOV'{yy}", "Dec": f"DEC'{yy}"
    }
    df_m_agg["Month_Header"] = df_m_agg["Month"].map(month_map)
    
    # Pivot data bulanan agar nama bulan menjadi kolom
    # (Di sini kita ambil QTY IN, PASS, FAIL. Nanti akan kita susun vertikal)
    
    # -------------------------------------------------------------
    # 3. FILTER & AGREGASI DATA MINGGUAN
    # -------------------------------------------------------------
    # Kita asumsikan df_weekly_detail memiliki kolom: Customer, Week, TOTAL QTY IN, PASS, FAIL
    df_w = df_weekly_detail[df_weekly_detail["Customer"].isin(target_customers)].copy()
    
    df_w_agg = df_w.groupby(["Customer", "Week"], as_index=False)[
        ["TOTAL QTY IN", "TOTAL QTY PASS", "TOTAL QTY FAIL"]
    ].sum()
    # Format Week asumsikan sudah berupa "WW01", "WW02", dst.
    
    # -------------------------------------------------------------
    # 4. MEMBANGUN STRUKTUR TABEL FINAL (WIDE FORMAT)
    # -------------------------------------------------------------
    # Di Pandas, cara paling rapi untuk membuat format tabel seperti excel milikmu
    # adalah dengan membuat dictionary/list of rows lalu mengubahnya jadi DataFrame.
    
    final_rows = []
    
    # Urutan bulan standard untuk Q1, Q2, Q3, Q4
    q1_months = ["Jan", "Feb", "Mar"]
    q2_months = ["Apr", "May", "Jun"]
    q3_months = ["Jul", "Aug", "Sep"]
    q4_months = ["Oct", "Nov", "Dec"]
    all_months = q1_months + q2_months + q3_months + q4_months
    
    # List mingguan (1-53) diformat "WW01" s/d "WW53"
    all_weeks = [f"WW{str(i).zfill(2)}" for i in range(1, 54)]
    
    for cust in target_customers:
        # Tarik data customer ini saja
        m_data = df_m_agg[df_m_agg["Customer"] == cust]
        w_data = df_w_agg[df_w_agg["Customer"] == cust]
        
        # Buat dictionary untuk menampung qty sementara
        tested, passed, rejected = {}, {}, {}
        
        # Isi data bulanan
        for m in all_months:
            row_m = m_data[m_data["Month"] == m]
            tested[m] = row_m["TOTAL QTY IN"].sum() if not row_m.empty else 0
            passed[m] = row_m["TOTAL QTY PASS"].sum() if not row_m.empty else 0
            rejected[m] = row_m["TOTAL QTY FAIL"].sum() if not row_m.empty else 0
            
        # Isi data mingguan
        for w in all_weeks:
            row_w = w_data[w_data["Week"] == w] # Sesuaikan format Week ("WW01" atau "WWK01")
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
        
        # Helper function untuk format kolom
        def create_metric_row(metric_name, data_dict, is_yield=False):
            # Susun sesuai urutan kolom yang kamu mau
            row = {"Metric": metric_name, "CUSTOMER": cust if metric_name == "Total qty tested" else ""}
            
            # Helper ambil value
            def get_val(key):
                if not is_yield:
                    # Tampilkan angka bulat, jika 0 tampilkan 0 (atau "-" jika mau)
                    return int(data_dict.get(key, 0))
                else:
                    # Kalau Yield = Passed/Tested
                    t = tested.get(key, 0)
                    p = passed.get(key, 0)
                    if t > 0:
                        return f"{(p/t)*100:.2f}%"
                    else:
                        return "#DIV/0!" # Sesuai format excelmu
            
            # --- SUSUNAN KOLOM ---
            # Q1 Group
            row[f"JAN'{yy}"] = get_val("Jan")
            for w in [f"WW{str(i).zfill(2)}" for i in range(1, 5)]: row[w] = get_val(w)
            
            row[f"FEB'{yy}"] = get_val("Feb")
            for w in [f"WW{str(i).zfill(2)}" for i in range(5, 9)]: row[w] = get_val(w)
            
            row[f"MAR'{yy}"] = get_val("Mar")
            for w in [f"WW{str(i).zfill(2)}" for i in range(9, 14)]: row[w] = get_val(w)
            row["Q1"] = get_val("Q1")
            
            # Q2 Group
            row[f"APR'{yy}"] = get_val("Apr")
            for w in [f"WW{str(i).zfill(2)}" for i in range(14, 18)]: row[w] = get_val(w)
            row[f"MAY'{yy}"] = get_val("May")
            for w in [f"WW{str(i).zfill(2)}" for i in range(18, 22)]: row[w] = get_val(w)
            row[f"JUN'{yy}"] = get_val("Jun")
            for w in [f"WW{str(i).zfill(2)}" for i in range(22, 27)]: row[w] = get_val(w)
            row["Q2"] = get_val("Q2")
            
            # Q3 Group
            row[f"JUL'{yy}"] = get_val("Jul")
            for w in [f"WW{str(i).zfill(2)}" for i in range(27, 31)]: row[w] = get_val(w)
            row[f"AUG'{yy}"] = get_val("Aug")
            for w in [f"WW{str(i).zfill(2)}" for i in range(31, 35)]: row[w] = get_val(w)
            row[f"SEP'{yy}"] = get_val("Sep")
            for w in [f"WW{str(i).zfill(2)}" for i in range(35, 39)]: row[w] = get_val(w)
            row["Q3"] = get_val("Q3")
            
            # Q4 Group
            row[f"OCT'{yy}"] = get_val("Oct")
            for w in [f"WW{str(i).zfill(2)}" for i in range(39, 44)]: row[w] = get_val(w)
            row[f"NOV'{yy}"] = get_val("Nov")
            for w in [f"WW{str(i).zfill(2)}" for i in range(44, 48)]: row[w] = get_val(w)
            row[f"DEC'{yy}"] = get_val("Dec")
            for w in [f"WW{str(i).zfill(2)}" for i in range(48, 54)]: row[w] = get_val(w)
            row["Q4"] = get_val("Q4")
            
            # YTD
            row[f"{year_str} YTD"] = get_val("YTD")
            
            return row

        # Susun 4 baris per customer
        final_rows.append(create_metric_row("Total qty tested", tested, is_yield=False))
        final_rows.append(create_metric_row("Total qty passed", passed, is_yield=False))
        final_rows.append(create_metric_row("Total qty rejected", rejected, is_yield=False))
        final_rows.append(create_metric_row("Yield", None, is_yield=True)) # Pass dummy, krn is_yield=True akan panggil t & p global loop
        
    # Build dataframe akhir
    df_ict_report = pd.DataFrame(final_rows)
    
    # Render di Streamlit
    st.dataframe(df_ict_report, use_container_width=True, hide_index=True)
    
    # Info: Export button ke excel disiapkan untuk next step
    st.info("💡 Tombol Ekspor ke Excel (dengan sheet ICT, B, FCT) akan dibangun di tahap selanjutnya.")
  
