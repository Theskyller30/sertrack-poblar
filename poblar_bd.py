import os
import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

# Obtener las credenciales de la base de datos desde variables de entorno
DB_CONNECTION = os.environ.get('DB_CONNECTION', 'mysql')
DB_HOST = os.environ.get('DB_HOST', '190.109.19.165')
DB_PORT = os.environ.get('DB_PORT', 3306)
DB_DATABASE = os.environ.get('DB_DATABASE', 'sertrack')
DB_USERNAME = os.environ.get('DB_USERNAME', 'dev')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '1007264290.,0') 

DATABASE_URL = f'{DB_CONNECTION}://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}'
engine = create_engine(DATABASE_URL)

def actualizar_base_de_datos(archivo_excel, excel_date_column, excel_cantidad_column, 
                            excel_pedido_column, excel_motonave_column, excel_incoterms_column,
                            excel_cliente_column, excel_linea_naviera_column, excel_eta_mn_column,
                            excel_fecha_documental_column):
    try:
        # Especificar el tipo de dato de las columnas como str
        data_excel = pd.read_excel(archivo_excel, sheet_name='Sheet1', header=0, usecols=[
            excel_date_column, excel_cantidad_column, excel_pedido_column, excel_motonave_column,
            excel_incoterms_column, excel_cliente_column, excel_linea_naviera_column,
            excel_eta_mn_column, excel_fecha_documental_column
        ], dtype={
            excel_date_column: str, 
            excel_cantidad_column: str, 
            excel_pedido_column: str,
            excel_motonave_column: str,
            excel_incoterms_column: str, 
            excel_cliente_column: str, 
            excel_linea_naviera_column: str,
            excel_eta_mn_column: str,
            excel_fecha_documental_column: str
        })

        data_excel = data_excel[data_excel[excel_date_column] != 'Total']
        data_excel[excel_date_column] = data_excel[excel_date_column].astype(str).str.strip()

        try:
            data_excel[excel_date_column] = pd.to_datetime(data_excel[excel_date_column], format='%d/%m/%Y')
            data_excel[excel_date_column] = data_excel[excel_date_column].dt.strftime('%Y-%m-%d')
            # Convertir 'eta_mn' a formato de fecha YYYY-MM-DD
            data_excel[excel_eta_mn_column] = pd.to_datetime(data_excel[excel_eta_mn_column], format='%d/%m/%Y')
            data_excel[excel_eta_mn_column] = data_excel[excel_eta_mn_column].dt.strftime('%Y-%m-%d')
            # Convertir 'fecha_documental' a formato de fecha YYYY-MM-DD
            data_excel[excel_fecha_documental_column] = pd.to_datetime(data_excel[excel_fecha_documental_column], format='%d/%m/%Y')
            data_excel[excel_fecha_documental_column] = data_excel[excel_fecha_documental_column].dt.strftime('%Y-%m-%d')
        except ValueError:
            st.error("Error al convertir las fechas. Revisa el formato en la columna de Excel.")
            return

        data_excel['created_at'] = datetime.now()
        data_excel['updated_at'] = datetime.now()

        with engine.connect() as conn:
            for index, row in data_excel.iterrows():
                pedido = row[excel_pedido_column]
                fecha_programa = row[excel_date_column]
                cantidad_cont = row[excel_cantidad_column]
                motonave = row[excel_motonave_column]
                incoterms = row[excel_incoterms_column]
                cliente = row[excel_cliente_column]
                linea_naviera = row[excel_linea_naviera_column]
                eta_mn = row[excel_eta_mn_column]
                fecha_documental = row[excel_fecha_documental_column]

                try:
                    with conn.begin() as transaction:
                        # Insertar nuevo registro (ignorando duplicados)
                        query_insert = text(f"""
                            INSERT IGNORE INTO planeacion (pedido, fecha_programa, cantidad_cont, motonave, 
                                                          incoterms, cliente, linea_naviera, eta_mn, fecha_documental,
                                                          created_at, updated_at) 
                            VALUES ('{pedido}', '{fecha_programa}', '{cantidad_cont}', '{motonave}', 
                                    '{incoterms}', '{cliente}', '{linea_naviera}', '{eta_mn}', '{fecha_documental}',
                                    '{datetime.now()}', '{datetime.now()}')
                        """)
                        conn.execute(query_insert)

                        # Actualizar fecha_programa para todos los registros con el mismo pedido
                        query_update = text(f"""
                            UPDATE planeacion 
                            SET fecha_programa = '{fecha_programa}', 
                                incoterms = '{incoterms}', 
                                cliente = '{cliente}', 
                                linea_naviera = '{linea_naviera}', 
                                eta_mn = '{eta_mn}', 
                                fecha_documental = '{fecha_documental}',
                                updated_at = '{datetime.now()}'
                            WHERE pedido = '{pedido}'
                        """)
                        conn.execute(query_update)

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
    excel_incoterms_column = st.text_input("Nombre de la columna con INCOTERMS en Excel:", value="incoterms")
    excel_cliente_column = st.text_input("Nombre de la columna con CLIENTE en Excel:", value="cliente")
    excel_linea_naviera_column = st.text_input("Nombre de la columna con LINEA NAVIERA en Excel:", value="linea_naviera")
    excel_eta_mn_column = st.text_input("Nombre de la columna con ETA MN en Excel:", value="eta_mn")
    excel_fecha_documental_column = st.text_input("Nombre de la columna con FECHA DOCUMENTAL en Excel:", value="fecha_documental")

if st.button("Poblar") and archivo_excel is not None:
    actualizar_base_de_datos(archivo_excel, excel_date_column, excel_cantidad_column, 
                            excel_pedido_column, excel_motonave_column, excel_incoterms_column,
                            excel_cliente_column, excel_linea_naviera_column, excel_eta_mn_column,
                            excel_fecha_documental_column)