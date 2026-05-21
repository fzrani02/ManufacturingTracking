import streamlit as st
import pandas as pd

# 1. Konfigurasi Halaman Dashboard
st.set_page_config(
    page_title="Manufacturing Tracking Dashboard", 
    layout="wide" # Agar tabel tampil lebar memenuhi layar
)

st.title("🏭 Manufacturing Tracking Dashboard")
st.write("Please double-click on the table cell below to enter or edit data.")

# 2. Inisialisasi Data (Session State)
# Ini penting agar data tidak hilang setiap kali Anda berinteraksi dengan dashboard
if "df" not in st.session_state:
    # Membuat tabel kosong dengan judul kolom sesuai permintaan Anda
    kolom = [
        "No", 
        "Customer", 
        "Problem Description", 
        "Picture", 
        "Detection", 
        "Process/Material/Test Related/Workmanship", 
        "Feedback", 
        "Analysis", 
        "Status", 
        "Remarks"
    ]
    st.session_state.df = pd.DataFrame(columns=kolom)

# 3. Menampilkan Editable Table (Tabel yang bisa diedit)
st.subheader("Tabel Data Issue / Quality")

# st.data_editor adalah fitur Streamlit untuk tabel interaktif
edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic", # Memungkinkan Anda menambah baris baru dengan klik tanda "+" di bawah tabel
    use_container_width=True, # Mengisi lebar layar penuh
    column_config={
        "No": st.column_config.NumberColumn("No", step=1),
        # Konfigurasi kolom paragraf (text panjang)
        "Problem Description": st.column_config.TextColumn("Problem Description", max_chars=2000),
        "Analysis": st.column_config.TextColumn("Analysis", max_chars=2000),
        "Remarks": st.column_config.TextColumn("Remarks", max_chars=2000),
        # Konfigurasi kolom Status agar jadi Dropdown pilihan
        "Status": st.column_config.SelectboxColumn(
            "Status",
            options=["Open", "In Progress", "Closed"],
            required=False,
        )
    }
)

# Menyimpan perubahan kembali ke sistem (session state)
st.session_state.df = edited_df

# 4. Fitur Upload Gambar Pendukung
st.divider() # Garis pemisah
st.subheader("📎 Upload Gambar")
st.info("💡 Since you can't upload images directly into the table cells, please upload the image here, then enter the image name in the ‘Picture’ column in the table above.")

uploaded_file = st.file_uploader("Choose Problem Picture)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Menampilkan gambar yang baru diupload
    st.success(f"Gambar '{uploaded_file.name}' berhasil dimuat!")
    st.image(uploaded_file, caption=uploaded_file.name, width=400)
