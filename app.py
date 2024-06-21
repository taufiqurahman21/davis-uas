import streamlit as st
import mysql.connector
import pandas as pd
from mysql.connector import Error

# Fungsi untuk mendapatkan koneksi database
@st.cache(allow_output_mutation=True)
def get_database_connection():
    try:
        conn = mysql.connector.connect(
            host=st.secrets["DB_HOST"],
            port=st.secrets["DB_PORT"],
            user=st.secrets["DB_USER"],
            passwd=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_NAME"]
        )
        return conn
    except Error as e:
        st.error(f"Error connecting to MySQL database: {e}")
        raise e

# Fungsi untuk mendapatkan data dari database
def get_data(query):
    conn = get_database_connection()
    try:
        return pd.read_sql(query, conn)
    except Error as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()  # Tutup koneksi setelah selesai digunakan

# Query untuk data perbandingan (comparison)
query_comparison = """
SELECT 
    dpc.EnglishProductCategoryName AS CategoryName, 
    SUM(fis.SalesAmount) AS TotalSalesAmount,
    'comparison' AS Data_Type
FROM 
    factinternetsales fis
JOIN 
    dimproduct dp ON fis.ProductKey = dp.ProductKey
JOIN 
    dimproductsubcategory dpsc ON dp.ProductSubcategoryKey = dpsc.ProductSubcategoryKey
JOIN 
    dimproductcategory dpc ON dpsc.ProductCategoryKey = dpc.ProductCategoryKey
GROUP BY 
    CategoryName
ORDER BY 
    TotalSalesAmount DESC;
"""

# Query untuk data hubungan (relationship)
query_relationship = """
SELECT 
    pr.EnglishPromotionName AS PromotionName, 
    dpc.EnglishProductCategoryName AS CategoryName, 
    fis.SalesAmount,
    'relationship' AS Data_Type
FROM 
    factinternetsales fis
JOIN 
    dimproduct dp ON fis.ProductKey = dp.ProductKey
JOIN 
    dimproductsubcategory dpsc ON dp.ProductSubcategoryKey = dpsc.ProductSubcategoryKey
JOIN 
    dimproductcategory dpc ON dpsc.ProductCategoryKey = dpc.ProductCategoryKey
JOIN 
    dimpromotion pr ON fis.PromotionKey = pr.PromotionKey;
"""

# Query untuk data komposisi (composition)
query_composition = """
SELECT 
    pc.EnglishProductCategoryName AS CategoryName,
    dst.SalesTerritoryRegion AS Wilayah, 
    SUM(fis.SalesAmount) AS TotalSalesAmount,
    'composition' AS Data_Type
FROM 
    factinternetsales fis
JOIN 
    dimproduct dp ON fis.ProductKey = dp.ProductKey
JOIN 
    dimproductsubcategory dpsc ON dp.ProductSubcategoryKey = dpsc.ProductSubcategoryKey
JOIN 
    dimproductcategory pc ON dpsc.ProductCategoryKey = pc.ProductCategoryKey
JOIN
    dimsalesterritory dst ON fis.SalesTerritoryKey = dst.SalesTerritoryKey
GROUP BY 
    CategoryName, Wilayah;
"""

# Query untuk data distribusi (distribution)
query_distribution = """
SELECT 
    fis.SalesAmount, 
    pc.EnglishProductCategoryName AS ProductCategory,
    fis.TaxAmt AS Pajak,
    'distribution' AS Data_Type
FROM 
    factinternetsales fis
JOIN 
    dimproduct dp ON fis.ProductKey = dp.ProductKey
JOIN 
    dimproductsubcategory dpsc ON dp.ProductSubcategoryKey = dpsc.ProductSubcategoryKey
JOIN 
    dimproductcategory pc ON dpsc.ProductCategoryKey = pc.ProductCategoryKey;
"""

# Sidebar
st.sidebar.title('Data Visualization Dashboard')
tab_selection = st.sidebar.selectbox("Pilih Tab:", ["Data Warehouse", "IMDB"])

if tab_selection == "Data Warehouse":
    # Filter berdasarkan kategori produk
    st.sidebar.header("Filter: ")
    category_filter = st.sidebar.multiselect(
        "Pilih Kategori Produk", 
        options=data_composition["CategoryName"].unique(),
        default=data_composition["CategoryName"].unique()
    )

    # Mengambil data dari database
    data_comparison = get_data(query_comparison)
    data_relationship = get_data(query_relationship)
    data_composition = get_data(query_composition)
    data_distribution = get_data(query_distribution)

    # Filter data berdasarkan pilihan di sidebar
    data_comparison_filtered = data_comparison[data_comparison["CategoryName"].isin(category_filter)]
    data_relationship_filtered = data_relationship[data_relationship["CategoryName"].isin(category_filter)]
    data_composition_filtered = data_composition[data_composition["CategoryName"].isin(category_filter)]
    data_distribution_filtered = data_distribution[data_distribution["ProductCategory"].isin(category_filter)]

    # Fungsi untuk menampilkan grafik perbandingan
    def comparison_graph():
        fig_comparison = px.bar(
            data_comparison_filtered, 
            x='CategoryName', 
            y='TotalSalesAmount', 
            title='Jumlah Penjualan berdasarkan Kategori Produk',
            labels={'CategoryName': 'Kategori Produk', 'TotalSalesAmount': 'Jumlah Penjualan'}
        )
        st.plotly_chart(fig_comparison)
        # Analysis di sini

    # Fungsi untuk menampilkan grafik hubungan
    def relationship_graph():
        fig_relationship = px.scatter(
            data_relationship_filtered, 
            x='PromotionName', 
            y='SalesAmount', 
            color='CategoryName', 
            title='Jumlah Penjualan berdasarkan Promosi dan Produk',
            labels={'PromotionName': 'Nama Promosi', 'SalesAmount': 'Jumlah Penjualan', 'CategoryName': 'Kategori Produk'}
        )
        st.plotly_chart(fig_relationship)
        # Analysis di sini

    # Fungsi untuk menampilkan grafik komposisi
    def composition_graph():
        fig_composition = px.pie(
            data_composition_filtered, 
            names='Wilayah', 
            values='TotalSalesAmount', 
            title='Komposisi Penjualan berdasarkan Kategori dan Wilayah',
            labels={'CategoryName': 'Nama Kategori', 'TotalSalesAmount': 'Jumlah Penjualan', 'Wilayah': 'Wilayah'}
        )
        st.plotly_chart(fig_composition)
        # Analysis di sini

    # Fungsi untuk menampilkan grafik distribusi
    def distribution_graph():
        fig_distribution = px.histogram(
            data_distribution_filtered, 
            x='SalesAmount', 
            color='ProductCategory',
            nbins=50,  # Jumlah bins
            title='Distribusi Jumlah Penjualan berdasarkan Kategori Produk',
            labels={'SalesAmount': 'Jumlah Penjualan', 'ProductCategory': 'Kategori Produk'},
            barmode='overlay'
        )
        st.plotly_chart(fig_distribution)
        # Analysis di sini

    # Tampilan grafik
    comparison_graph()
    relationship_graph()
    composition_graph()
    distribution_graph()

elif tab_selection == 'IMDB':
    # Implementasi IMDB akan ada di sini
    pass
