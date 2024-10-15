# PRUEBA______DIRECTO A SERTRACK_BD

import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

DB_CONNECTION = 'mysql'
DB_HOST = '190.109.19.165'
DB_PORT = 3306
DB_DATABASE = 'sertrack'
DB_USERNAME = 'dev'
DB_PASSWORD = '1007264290.,0' 

DATABASE_URL = f'{DB_CONNECTION}://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}'
engine = create_engine(DATABASE_URL)

def actualizar_base_de_datos(archivo_excel, excel_date_column, excel_cantidad_column, 
                            excel_pedido_column, excel_motonave_column):
    try:
        data_excel = pd.read_excel(archivo_excel, sheet_name='Sheet1', header=0, usecols=[
            excel_date_column, excel_cantidad_column, excel_pedido_column, excel_motonave_column
        ], dtype={
            excel_date_column: str, 
            excel_cantidad_column: str, 
            excel_pedido_column: str, 
            excel_motonave_column: str
        })

        data_excel = data_excel[data_excel[excel_date_column] != 'Total']
        data_excel[excel_date_column] = data_excel[excel_date_column].astype(str).str.strip()

        try:
            data_excel[excel_date_column] = pd.to_datetime(data_excel[excel_date_column], format='%d/%m/%Y')
            data_excel[excel_date_column] = data_excel[excel_date_column].dt.strftime('%Y-%m-%d')
        except ValueError:
            st.error("Error al convertir las fechas. Revisa el formato en la columna de Excel.")
            return

        data_excel['created_at'] = datetime.now()
        data_excel['updated_at'] = datetime.now()

        with engine.connect() as conn:
            for index, row in data_excel.iterrows():
                pedido = row[excel_pedido_column]
                fecha_programa = row[excel_date_column]

                try:
                    with conn.begin() as transaction:
                        query = text(f"SELECT 1 FROM planeacion WHERE pedido = '{pedido}'")
                        result = conn.execute(query).fetchone()

                        if result:
                            update_query = text(f"""
                                UPDATE planeacion 
                                SET fecha_programa = '{fecha_programa}', updated_at = '{datetime.now()}' 
                                WHERE pedido = '{pedido}'
                            """)
                            conn.execute(update_query)
                        else:
                            new_row = pd.DataFrame([row])
                            new_row.to_sql('planeacion', conn, if_exists='append', index=False)
                except Exception as e:
                    st.error(f"Error al actualizar la base de datos: {e}")
                    transaction.rollback()
                    return

        st.success("Actualización de la base de datos exitosa!")

    except Exception as e:
        st.error(f"Error general: {e}")

st.title("Actualizar BD desde Excel")
archivo_excel = st.file_uploader("Selecciona el archivo Excel (.xlsx)", type="xlsx")

with st.expander("Configuración de columnas"):
    excel_date_column = st.text_input("Nombre de la columna con la fecha en Excel:", value="fecha_programa")
    excel_cantidad_column = st.text_input("Nombre de la columna con la cantidad en Excel:", value="cantidad_cont")
    excel_pedido_column = st.text_input("Nombre de la columna con PEDIDO en Excel:", value="pedido")
    excel_motonave_column = st.text_input("Nombre de la columna con MOTONAVE en Excel:", value="motonave")

if st.button("Poblar") and archivo_excel is not None:
    actualizar_base_de_datos(archivo_excel, excel_date_column, excel_cantidad_column, excel_pedido_column, excel_motonave_column)