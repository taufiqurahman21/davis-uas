import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from numerize.numerize import numerize
import re

# Konfigurasi halaman
st.set_page_config(
    page_title="Data Visualization Dashboard",
    page_icon="📌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ambil informasi dari secrets
mysql_secrets = st.secrets["mysql"]

# Ambil informasi dari secrets
DB_HOST = mysql_secrets["DB_HOST"]
DB_PORT = mysql_secrets["DB_PORT"]
DB_USER = mysql_secrets["DB_USER"]
DB_PASSWORD = mysql_secrets["DB_PASSWORD"]
DB_NAME = mysql_secrets["DB_NAME"]

# Buat koneksi ke database
try:
    db_connection = pymysql.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    # Sekarang Anda memiliki koneksi database yang siap digunakan
    # Lakukan operasi database seperti menjalankan query di sini

    # Contoh menjalankan query
    with db_connection.cursor() as cursor:
        sql_query = "SELECT * FROM nama_tabel;"
        cursor.execute(sql_query)
        result = cursor.fetchall()
        print(result)

except Exception as e:
    print(f"Error connecting to the database or executing query: {str(e)}")
finally:
    if 'db_connection' in locals() or 'db_connection' in globals():
        db_connection.close()  # pastikan untuk selalu menutup koneksi setelah selesai

# Fungsi untuk mengambil data dari database
def get_data(query):
    try:
        return pd.read_sql(query, db_connection)
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()

#  Query untuk data perbandingan (comparison)
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

# Mengambil data dari database
data_comparison = get_data(query_comparison)
data_relationship = get_data(query_relationship)
data_composition = get_data(query_composition)
data_distribution = get_data(query_distribution)

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
        with st.expander("Analysis", expanded=False):
            if not data_comparison_filtered.empty:
                total_sales = data_comparison_filtered["TotalSalesAmount"].sum()
                top_product = data_comparison_filtered.loc[data_comparison_filtered["TotalSalesAmount"].idxmax()]["CategoryName"]
                st.markdown('**Total Penjualan**')
                st.write("Grafik ini menunjukkan perbandingan jumlah penjualan produk berdasarkan kategori produk dan tahun. Kategori produk yang ditampilkan dalam grafik ini adalah sepeda, pakaian, dan aksesoris.")
                st.write(f"Total penjualan untuk produk yang dipilih adalah {numerize(total_sales)}.")
                st.write(f"Produk dengan penjualan tertinggi adalah {top_product} dengan jumlah penjualan {numerize(data_comparison_filtered['TotalSalesAmount'].max())}.")
            else:
                st.write("Tidak ada data yang sesuai dengan filter.")

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
        with st.expander("Analysis", expanded=False):
            if not data_relationship_filtered.empty:
                correlation = data_relationship_filtered['SalesAmount'].corr(data_relationship_filtered['SalesAmount'])
                total_promotions = data_relationship_filtered['PromotionName'].nunique()
                highest_sales = data_relationship_filtered["SalesAmount"].max()
                highest_sales_promotion = data_relationship_filtered[data_relationship_filtered["SalesAmount"] == highest_sales]["PromotionName"].values[0]
                st.markdown('**Scatter Plot Analysis**')
                st.write("Grafik ini menunjukkan hubungan antara jumlah penjualan dan promosi untuk berbagai kategori produk. Kategori produk yang ditampilkan dalam grafik ini adalah sepeda, pakaian,")
                st.write(f"Korelasi antara jumlah penjualan dan promosi adalah {correlation:.2f}.")
                st.write(f"Ada {total_promotions} jenis promosi yang diterapkan untuk produk yang dipilih.")
                st.write(f"Promosi dengan penjualan tertinggi adalah **{highest_sales_promotion}** dengan penjualan sebesar **{highest_sales}**.")
            else:
                st.write("Tidak ada data yang sesuai dengan filter.")

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
        with st.expander("Analysis", expanded=False):
            if not data_composition_filtered.empty:
                total_sales = data_composition_filtered["TotalSalesAmount"].sum()
                highest_sales = data_composition_filtered["TotalSalesAmount"].max()
                highest_sales_category = data_composition_filtered[data_composition_filtered["TotalSalesAmount"] == highest_sales]["CategoryName"].values[0]
                highest_sales_region = data_composition_filtered[data_composition_filtered["TotalSalesAmount"] == highest_sales]["Wilayah"].values[0]
                st.markdown('**Donut Chart Analysis**')
                for index, row in data_composition_filtered.iterrows():
                    percentage = (row["TotalSalesAmount"] / total_sales) * 100
                    st.write(f"- **{row['CategoryName']}** di **{row['Wilayah']}**: {percentage:.2f}% dari total penjualan.")
                st.write(f"Kategori dengan penjualan tertinggi adalah **{highest_sales_category}** dengan penjualan sebesar **{highest_sales}**.")
                st.write(f"Wilayah dengan penjualan tertinggi adalah **{highest_sales_region}** dengan penjualan sebesar **{highest_sales}**.")
            else:
                st.write("Tidak ada data yang sesuai dengan filter.")

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
        
        with st.expander("Analysis", expanded=False):
            if not data_distribution_filtered.empty:
                highest_sales = data_distribution_filtered["SalesAmount"].max()
                highest_sales_category = data_distribution_filtered[data_distribution_filtered["SalesAmount"] == highest_sales]["ProductCategory"].values[0]
                total_sales = data_distribution_filtered["SalesAmount"].sum()
                
                highest_tax = data_distribution_filtered["Pajak"].max()
                highest_tax_category = data_distribution_filtered[data_distribution_filtered["Pajak"] == highest_tax]["ProductCategory"].values[0]
                total_tax = data_distribution_filtered["Pajak"].sum()

                st.markdown('**Histogram Analysis**')
                st.write("Grafik ini menunjukkan distribusi jumlah penjualan produk sepeda di Amerika Serikat berdasarkan kategori produk. Kategori produk yang ditampilkan dalam grafik ini adalah sepeda, pakaian, dan aksesoris.")
                st.write(f"Jumlah penjualan tertinggi adalah {numerize(highest_sales)} dalam kategori {highest_sales_category}.")
                st.write(f"Total penjualan adalah {numerize(total_sales)}.")
                
                st.write(f"Jumlah pajak tertinggi adalah {numerize(highest_tax)} dalam kategori {highest_tax_category}.")
                st.write(f"Total pajak adalah {numerize(total_tax)}.")
                
                st.write("Histogram menunjukkan distribusi jumlah penjualan dan pajak untuk setiap kategori produk.")
            else:
                st.write("Tidak ada data yang sesuai dengan filter.")

    # Tampilan grafik
    comparison_graph()
    relationship_graph()
    composition_graph()
    distribution_graph()

elif tab_selection == 'IMDB':
    # Membaca data dari file CSV
    df = pd.read_csv('movies250_combined_data.csv')

    # Sidebar
    st.sidebar.title('Filter Film')
    # Filter berdasarkan tahun
    year_filter = st.sidebar.multiselect(
        "Pilih Tahun",
        options=df['Year'].unique(),
        default=df['Year'].unique()
    )
    # Filter berdasarkan rating
    rating_filter = st.sidebar.multiselect(
        "Pilih Rating",
        options=df['Rating'].unique(),
        default=df['Rating'].unique()
    )

    # Filter data berdasarkan pilihan di sidebar
    df_filtered = df[(df['Year'].isin(year_filter)) & (df['Rating'].isin(rating_filter))]

    # Pastikan 'Durasi(Menit)' adalah numerik
    df_filtered['Durasi(Menit)'] = df_filtered['Durasi(Menit)'].astype(float)

    # Group by 'Rating' dan hitung rata-rata 'Durasi(Menit)'
    df_grouped = df_filtered.groupby('Rating')['Durasi(Menit)'].mean().reset_index()

    # Plot
    fig1 = px.bar(df_grouped, x='Rating', y='Durasi(Menit)', title='Rata-rata Durasi Film berdasarkan Rating')
    st.plotly_chart(fig1)

    with st.expander("Analysis", expanded=False):
        if not df_grouped.empty:
            max_duration = df_grouped['Durasi(Menit)'].max()
            max_duration_rating = df_grouped[df_grouped['Durasi(Menit)'] == max_duration]['Rating'].values[0]
            st.markdown('**Bar Chart Analysis**')
            st.write("Grafik ini menunjukkan perbandingan rata-rata durasi film berdasarkan rating film. Rating film yang ditampilkan dalam grafik ini adalah Approved, G, NC-17, Not Rated, PG, PG-13, Passed, dan R.")
            st.write(f"Durasi film tertinggi adalah {max_duration} menit dengan rating {max_duration_rating}.")
            st.write(f"Film dengan rating {max_duration_rating} cenderung memiliki durasi lebih panjang dibandingkan rating lainnya.")
            st.write(f"Rating {max_duration_rating} mungkin digunakan untuk film dengan plot yang lebih kompleks dan cerita yang lebih panjang.")
        else:
            st.write("Tidak ada data yang sesuai dengan filter.")

    # Relationship: Scatter Plot untuk Rating dan Gross US
    fig2 = px.scatter(df_filtered, x='Rating', y='Gross_US', title='Hubungan antara Rating dan Gross US', hover_name='Name')
    st.plotly_chart(fig2)
    with st.expander("Analysis", expanded=False):
        if not df_filtered.empty:
            correlation = df_filtered['Gross_US'].corr(df_filtered['Gross_US'])
            highest_gross = df_filtered['Gross_US'].max()
            highest_gross_movie = df_filtered[df_filtered['Gross_US'] == highest_gross]['Name'].values[0]
            st.markdown('**Scatter Plot Analysis**')
            st.write(f"Korelasi antara rating dan gross US adalah {correlation:.2f}.")
            st.write(f"Film dengan pendapatan tertinggi adalah {highest_gross_movie} dengan pendapatan {highest_gross}.")
            st.write(f"Dari grafik, kita bisa melihat apakah ada pola tertentu dalam distribusi pendapatan berdasarkan rating.")
            st.write(f"Rating yang lebih tinggi mungkin menunjukkan kualitas film yang lebih baik, yang berpotensi menarik lebih banyak penonton dan menghasilkan pendapatan yang lebih tinggi.")
        else:
            st.write("Tidak ada data yang sesuai dengan filter.")

    # Composition: Pie Chart untuk Distribusi Rating
    fig3 = px.pie(df_filtered, names='Rating', title='Composition Rating Film')
    st.plotly_chart(fig3)

    with st.expander("Analysis", expanded=False):
        if not df_filtered.empty:
            rating_count = df_filtered['Rating'].value_counts()
            total_movies = len(df_filtered)
            st.markdown('**Pie Chart Analysis**')
            for rating, count in rating_count.items():
                percentage = (count / total_movies) * 100
                st.write(f"Rating {rating}: {percentage:.2f}% dari total film.")
            st.write(f"Distribusi rating dalam film bisa mencerminkan preferensi penonton dan kualitas produksi film.")
            st.write(f"Film dengan rating tinggi mungkin menunjukkan kualitas produksi yang baik dan penerimaan positif dari penonton.")
            st.write(f"Sebaliknya, film dengan rating rendah mungkin menunjukkan kualitas produksi yang kurang dan penerimaan negatif dari penonton.")
            
            # Analisis tambahan
            st.write(f"Rating R atau Restricted biasanya diberikan untuk film yang mengandung konten dewasa, kekerasan, atau bahasa yang kasar. Tingginya persentase film dengan rating R dapat menunjukkan tren industri dalam menghasilkan film-film yang lebih berani dan eksplisit.")
            st.write(f"Rating PG-13 adalah salah satu rating yang paling umum, menandakan bahwa film tersebut cocok untuk penonton usia 13 tahun ke atas dengan beberapa pengawasan orang tua. Film dengan rating ini sering kali dibuat untuk menarik penonton dari berbagai kelompok usia.")
            st.write(f"Film dengan rating G atau General Audiences cocok untuk semua umur dan biasanya merupakan film keluarga atau animasi. Rendahnya persentase film dengan rating G bisa menunjukkan bahwa industri film cenderung fokus pada konten yang lebih kompleks dan menarik bagi audiens yang lebih tua.")
        else:
            st.write("Tidak ada data yang sesuai dengan filter.")

    # Distribution: Histogram untuk Durasi Film
    fig4 = px.histogram(df_filtered, x='Durasi(Menit)', title='Distribusi Durasi Film')
    st.plotly_chart(fig4)
    with st.expander("Analysis", expanded=False):
        if not df_filtered.empty:
            min_duration = df_filtered['Durasi(Menit)'].min()
            max_duration = df_filtered['Durasi(Menit)'].max()
            avg_duration = df_filtered['Durasi(Menit)'].mean()
            st.markdown('**Histogram Analysis**')
            st.write(f"Durasi film terpendek adalah {min_duration} menit.")
            st.write(f"Durasi film terpanjang adalah {max_duration} menit.")
            st.write(f"Rata-rata durasi film adalah {avg_duration:.2f} menit.")
            st.write(f"Histogram menunjukkan distribusi durasi film, memungkinkan kita melihat kecenderungan umum dalam durasi film.")
            st.write(f"Durasi film mungkin dipengaruhi oleh genre, plot, dan target audiens.")
        else:
            st.write("Tidak ada data yang sesuai dengan filter.")
